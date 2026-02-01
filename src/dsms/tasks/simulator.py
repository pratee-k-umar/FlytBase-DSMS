"""
Simulator Tasks
Celery tasks for drone simulation.
"""

import time
from datetime import datetime

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from pymongo.errors import AutoReconnect, NetworkTimeout, ServerSelectionTimeoutError

from dsms.db import connect_db
from dsms.simulator.engine import DroneSimulator

# Ensure DB connection
connect_db()

from dsms.models import Mission
from dsms.services import fleet_service, mission_service, telemetry_service


def retry_on_db_error(func, max_retries=3, delay=1.0):
    """Retry a database operation if it fails due to network issues"""
    for attempt in range(max_retries):
        try:
            return func()
        except (AutoReconnect, NetworkTimeout, ServerSelectionTimeoutError) as e:
            if attempt < max_retries - 1:
                print(
                    f"[RETRY] DB error, retrying in {delay}s... (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)
            else:
                print(f"[ERROR] DB operation failed after {max_retries} attempts: {e}")
                raise


@shared_task(bind=True)
def run_mission_simulation(self, mission_id: str):
    """
    Run drone simulation for a mission.
    This task simulates the drone flying the mission path
    and broadcasts telemetry updates via WebSocket.
    """
    print(f"Starting simulation for mission {mission_id}")

    try:
        # Get mission
        mission = mission_service.get_mission(mission_id)

        if mission.status != "in_progress":
            print(f"Mission {mission_id} is not in progress, skipping simulation")
            return

        # Initialize simulator
        simulator = DroneSimulator(mission)

        # Get channel layer for WebSocket broadcasts
        channel_layer = get_channel_layer()
        room_group_name = f"mission_{mission_id}"

        # Simulation loop
        tick_interval = 1.0  # seconds

        while True:
            # Check if mission is still in progress
            mission.reload()

            if mission.status == "paused":
                print(f"Mission {mission_id} paused, stopping simulation")
                break

            if mission.status == "aborted":
                print(f"Mission {mission_id} aborted, stopping simulation")
                break

            if mission.status != "in_progress":
                break

            # Run simulation tick
            result = simulator.tick(tick_interval)

            # Record telemetry
            telemetry_data = {
                "mission_id": mission_id,
                "drone_id": mission.drone.drone_id,
                "timestamp": datetime.utcnow(),
                "location": {"type": "Point", "coordinates": result["position"]},
                "altitude": result["altitude"],
                "heading": result["heading"],
                "speed": result["speed"],
                "battery_level": result["battery"],
                "signal_strength": 95,
                "current_waypoint_index": result["current_waypoint"],
                "distance_traveled": result["distance_traveled"],
                "progress": result["progress"],
            }

            telemetry_service.record_telemetry(telemetry_data)

            # Update mission progress
            mission.progress = result["progress"]
            mission.current_waypoint_index = result["current_waypoint"]
            mission.save()

            # Update drone location
            fleet_service.update_drone_location(
                mission.drone.drone_id, telemetry_data["location"], result["battery"]
            )

            # Broadcast telemetry via WebSocket
            try:
                async_to_sync(channel_layer.group_send)(
                    room_group_name,
                    {
                        "type": "telemetry_update",
                        "data": {
                            "location": result["position"],
                            "altitude": result["altitude"],
                            "heading": result["heading"],
                            "speed": result["speed"],
                            "battery": result["battery"],
                            "progress": result["progress"],
                            "current_waypoint": result["current_waypoint"],
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    },
                )
            except Exception as e:
                print(f"WebSocket broadcast error: {e}")

            # Check if complete
            if result.get("complete"):
                print(f"[SUCCESS] Mission {mission_id} completed!")
                mission_service.complete_mission(mission_id)

                # Broadcast completion
                try:
                    async_to_sync(channel_layer.group_send)(
                        room_group_name,
                        {
                            "type": "mission_complete",
                            "data": {
                                "mission_id": mission_id,
                                "status": "completed",
                                "message": "Mission completed successfully",
                            },
                        },
                    )
                except Exception:
                    pass

                break

            # Wait for next tick
            time.sleep(tick_interval)

    except Exception as e:
        print(f"[ERROR] Simulation error for mission {mission_id}: {e}")

        # Mark mission as failed
        try:
            mission = mission_service.get_mission(mission_id)
            mission.status = "failed"
            mission.save()

            # Release drone
            if mission.drone:
                mission.drone.status = "available"
                mission.drone.save()
        except Exception:
            pass

        raise


@shared_task
def simulate_telemetry_batch(mission_id: str, duration_seconds: int = 60):
    """
    Generate a batch of simulated telemetry for testing.
    Useful for development without running the full simulation.
    """
    print(f"Generating {duration_seconds}s of telemetry for {mission_id}")

    mission = mission_service.get_mission(mission_id)
    simulator = DroneSimulator(mission)

    for i in range(duration_seconds):
        result = simulator.tick(1.0)

        telemetry_data = {
            "mission_id": mission_id,
            "drone_id": mission.drone.drone_id if mission.drone else "DRN-TEST",
            "location": {"type": "Point", "coordinates": result["position"]},
            "altitude": result["altitude"],
            "heading": result["heading"],
            "speed": result["speed"],
            "battery_level": result["battery"],
            "current_waypoint_index": result["current_waypoint"],
            "distance_traveled": result["distance_traveled"],
            "progress": result["progress"],
        }

        telemetry_service.record_telemetry(telemetry_data)

        if result.get("complete"):
            break

    print(f"Generated {i + 1} telemetry points for {mission_id}")


def run_mission_simulation_sync(mission_id: str):
    """
    Synchronous version of mission simulation (no Celery).
    Runs in a background thread when Celery is not available.
    """
    print(f"[SYNC] Starting simulation for mission {mission_id}")

    try:
        # Get mission
        mission = mission_service.get_mission(mission_id)

        if mission.status != "in_progress":
            print(
                f"[SYNC] Mission {mission_id} is not in progress, skipping simulation"
            )
            return

        # Initialize simulator
        simulator = DroneSimulator(mission)

        # Simulation loop
        tick_interval = 1.0  # seconds

        while True:
            # Check if mission is still in progress
            mission.reload()

            if mission.status == "paused":
                print(f"[SYNC] Mission {mission_id} paused, stopping simulation")
                break

            if mission.status == "aborted":
                print(f"[SYNC] Mission {mission_id} aborted, stopping simulation")
                break

            if mission.status != "in_progress":
                break

            # Run simulation tick
            result = simulator.tick(tick_interval)

            # Record telemetry with retry logic
            telemetry_data = {
                "mission_id": mission_id,
                "drone_id": mission.assigned_drone_id,
                "timestamp": datetime.utcnow(),
                "location": {"type": "Point", "coordinates": result["position"]},
                "altitude": result["altitude"],
                "heading": result["heading"],
                "speed": result["speed"],
                "battery_level": result["battery"],
                "signal_strength": 95,
                "current_waypoint_index": result["current_waypoint"],
                "distance_traveled": result["distance_traveled"],
                "progress": result["progress"],
            }

            # Retry telemetry recording on network errors
            try:
                retry_on_db_error(
                    lambda: telemetry_service.record_telemetry(telemetry_data)
                )
            except Exception as e:
                print(f"[SYNC] Failed to record telemetry: {e}")
                # Continue simulation even if telemetry fails

            # Update mission progress with retry
            try:
                retry_on_db_error(
                    lambda: (
                        setattr(mission, "progress", result["progress"]),
                        setattr(
                            mission,
                            "current_waypoint_index",
                            result["current_waypoint"],
                        ),
                        mission.save(),
                    )[-1]
                )
            except Exception as e:
                print(f"[SYNC] Failed to update mission progress: {e}")
                # Continue simulation even if update fails

            # Update drone location
            try:
                retry_on_db_error(
                    lambda: fleet_service.update_drone_location(
                        mission.assigned_drone_id,
                        telemetry_data["location"],
                        result["battery"],
                    )
                )
            except Exception as e:
                print(f"[SYNC] Could not update drone location: {e}")

            # Check if complete
            if result.get("complete"):
                print(f"[SYNC SUCCESS] Mission {mission_id} completed!")
                mission_service.complete_mission(mission_id)
                break

            # Wait for next tick
            time.sleep(tick_interval)

    except Exception as e:
        print(f"[SYNC ERROR] Simulation error for mission {mission_id}: {e}")
        import traceback

        traceback.print_exc()

        # Mark mission as failed
        try:
            mission = mission_service.get_mission(mission_id)
            mission.status = "failed"
            mission.save()

            # Release drone
            if mission.assigned_drone_id:
                try:
                    drone = Drone.objects.get(drone_id=mission.assigned_drone_id)
                    drone.status = "available"
                    drone.current_mission_id = None
                    drone.save()
                except Exception:
                    pass
        except Exception:
            pass


@shared_task(bind=True)
def charge_drone_task(self, drone_id: str):
    """
    Celery task to charge a drone to 100%.
    This runs in the Celery worker, ensuring it persists even if the web request ends.
    """
    from dsms.models import Drone
    
    CHARGE_RATE = 5.0  # % per second (fast for demo)
    MAX_CHARGE_TIME = 30  # Max 30 seconds to fully charge
    
    print(f"[CHARGING] Starting charge task for drone {drone_id}")
    
    for tick in range(MAX_CHARGE_TIME):
        try:
            drone = Drone.objects.get(drone_id=drone_id)
            
            if drone.battery_level >= 100:
                # Fully charged - set to available
                drone.status = "available"
                drone.battery_level = 100.0
                drone.save()
                print(f"[CHARGING] Drone {drone_id} fully charged and available")
                return {"status": "complete", "battery": 100}
                
            if drone.status != "charging":
                # Drone status changed externally, stop charging
                print(f"[CHARGING] Drone {drone_id} interrupted (status: {drone.status})")
                return {"status": "interrupted", "reason": drone.status}
            
            # Charge battery
            new_level = min(100, drone.battery_level + CHARGE_RATE)
            drone.battery_level = new_level
            drone.save()
            print(f"[CHARGING] Drone {drone_id}: {new_level:.1f}%")
            
            time.sleep(1)  # Update every second
            
        except Drone.DoesNotExist:
            print(f"[CHARGING] Drone {drone_id} not found")
            return {"status": "error", "reason": "drone_not_found"}
        except Exception as e:
            print(f"[CHARGING] Error for {drone_id}: {e}")
            return {"status": "error", "reason": str(e)}
    
    # If we get here, set to available anyway
    try:
        drone = Drone.objects.get(drone_id=drone_id)
        drone.status = "available"
        drone.battery_level = 100.0
        drone.save()
    except Exception:
        pass
    
    return {"status": "complete", "battery": 100}


def charge_drone_sync(drone_id: str):
    """
    Synchronous version of drone charging (for when Celery is not available).
    Runs in a background thread but charges quickly.
    """
    import threading
    from dsms.models import Drone
    
    def do_charge():
        CHARGE_RATE = 10.0  # % per second (very fast for sync mode)
        MAX_ITERATIONS = 15
        
        for _ in range(MAX_ITERATIONS):
            try:
                drone = Drone.objects.get(drone_id=drone_id)
                
                if drone.battery_level >= 100:
                    drone.status = "available"
                    drone.battery_level = 100.0
                    drone.save()
                    print(f"[SYNC CHARGING] Drone {drone_id} fully charged")
                    return
                    
                if drone.status != "charging":
                    print(f"[SYNC CHARGING] Drone {drone_id} interrupted")
                    return
                
                new_level = min(100, drone.battery_level + CHARGE_RATE)
                drone.battery_level = new_level
                drone.save()
                print(f"[SYNC CHARGING] Drone {drone_id}: {new_level:.1f}%")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"[SYNC CHARGING] Error: {e}")
                return
        
        # Force complete after max iterations
        try:
            drone = Drone.objects.get(drone_id=drone_id)
            drone.status = "available"
            drone.battery_level = 100.0
            drone.save()
        except Exception:
            pass
    
    thread = threading.Thread(target=do_charge, daemon=True)
    thread.start()
