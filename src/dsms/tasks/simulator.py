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


# Battery handoff thresholds
CRITICAL_BATTERY_LEVEL = 20  # Trigger handoff when battery drops below this %
MINIMUM_BATTERY_FOR_MISSION = 30  # Minimum battery to continue a mission


def abort_mission_no_replacement(mission, current_drone, channel_layer=None):
    """
    Abort mission when no replacement drone is available.
    Current drone returns to base for charging.
    
    Args:
        mission: The Mission object
        current_drone: The Drone that needs replacement
        channel_layer: WebSocket channel layer (optional)
        
    Returns:
        "aborted" status
    """
    from datetime import datetime
    from asgiref.sync import async_to_sync
    
    print(f"[ABORT] No replacement available for mission {mission.mission_id}")
    print(f"[ABORT] Drone {current_drone.drone_id} battery: {current_drone.battery_level}%")
    
    # Update mission status
    mission.status = "aborted"
    mission.abort_reason = f"No replacement drone available (battery critical: {current_drone.battery_level}%)"
    mission.save()
    
    # Send current drone back to base
    base_id = mission.origin_base_id or current_drone.base_id
    current_drone.status = "returning"
    current_drone.current_mission_id = None
    current_drone.save()
    
    # Start return flight
    try:
        simulate_return_flight.delay(
            current_drone.drone_id,
            base_id,
            current_drone.location.get("coordinates") if current_drone.location else None
        )
        print(f"[ABORT] {current_drone.drone_id} returning to base")
    except Exception as e:
        print(f"[ABORT] Could not start return flight: {e}")
        # Fallback
        current_drone.status = "charging"
        current_drone.save()
    
    # Log abort event
    try:
        from dsms.models import log_handoff
        from dsms.services import base_service
        
        base = None
        if base_id:
            try:
                base = base_service.get_base(base_id)
            except Exception:
                pass
        
        log_handoff(
            mission=mission,
            handoff_type="mission_aborted",
            outgoing_drone=current_drone,
            base=base,
            waypoint_index=mission.current_waypoint_index or 0,
            reason=f"No replacement available (battery: {current_drone.battery_level}%)"
        )
        print(f"[ABORT] Logged mission_aborted event")
    except Exception as e:
        print(f"[ABORT] Could not log abort: {e}")
    
    # Broadcast abort event
    if channel_layer:
        try:
            room_group_name = f"mission_{mission.mission_id}"
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    "type": "mission_aborted",
                    "data": {
                        "mission_id": mission.mission_id,
                        "drone_id": current_drone.drone_id,
                        "battery_level": current_drone.battery_level,
                        "reason": "No replacement drone available",
                        "drone_returning": True,
                        "base_id": base_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                },
            )
            print(f"[ABORT] Broadcast abort event via WebSocket")
        except Exception as e:
            print(f"[ABORT] WebSocket broadcast error: {e}")
    
    return "aborted"


def perform_battery_handoff(mission, current_drone, current_waypoint_index, channel_layer=None):
    """
    Perform a battery handoff - swap out low-battery drone for a replacement.
    
    Args:
        mission: The Mission object
        current_drone: The current Drone that needs to be replaced
        current_waypoint_index: Current waypoint index in the mission
        channel_layer: Optional channel layer for WebSocket broadcasts
        
    Returns:
        Drone: The replacement drone, or None if no replacement available
    """
    from dsms.models import Drone
    from dsms.services import mission_service
    
    room_group_name = f"mission_{mission.mission_id}"
    
    print(f"[HANDOFF] Battery critical ({current_drone.battery_level}%) for drone {current_drone.drone_id}")
    print(f"[HANDOFF] Mission {mission.mission_id} at waypoint {current_waypoint_index}")
    
    # Try to find a replacement drone from the SAME BASE
    replacement_drone = None
    origin_base_id = mission.origin_base_id or current_drone.base_id
    
    if origin_base_id:
        # First, try to find a drone from the same base
        same_base_drones = list(
            Drone.objects(
                base_id=origin_base_id,
                drone_id__ne=current_drone.drone_id,
                status="available"
            ).order_by("-battery_level")
        )
        
        for drone in same_base_drones:
            if drone.battery_level >= MINIMUM_BATTERY_FOR_MISSION:
                replacement_drone = drone
                print(f"[HANDOFF] Found replacement from same base: {drone.drone_id}")
                break
    
    # Fallback: Try any available drone
    if not replacement_drone:
        try:
            replacement_drone = mission_service.auto_assign_drone(mission)
            
            # Make sure we don't assign the same drone
            if replacement_drone.drone_id == current_drone.drone_id:
                available_drones = list(
                    Drone.objects(
                        drone_id__ne=current_drone.drone_id,
                        status="available"
                    ).order_by("-battery_level")
                )
                replacement_drone = available_drones[0] if available_drones else None
                
        except Exception as e:
            print(f"[HANDOFF] Could not find replacement: {e}")
            return None
    
    if not replacement_drone:
        print("[HANDOFF] No replacement drone available, continuing with current drone")
        return None
    
    # Check if replacement has sufficient battery
    if replacement_drone.battery_level < MINIMUM_BATTERY_FOR_MISSION:
        print(f"[HANDOFF] Replacement drone {replacement_drone.drone_id} has low battery ({replacement_drone.battery_level}%)")
        # Try to find another drone, or abort
        return abort_mission_no_replacement(mission, current_drone, channel_layer)
    
    print(f"[HANDOFF] Replacement drone: {replacement_drone.drone_id} (battery: {replacement_drone.battery_level}%)") # Get base info for logging
    base = None
    base_id = mission.origin_base_id or current_drone.base_id
    if base_id:
        try:
            from dsms.services import base_service
            base = base_service.get_base(base_id)
        except Exception:
            pass
    
    # Get current drone's location (handoff point)
    handoff_lat, handoff_lng = 0.0, 0.0
    if current_drone.location:
        loc = current_drone.location
        if "coordinates" in loc:
            handoff_lng, handoff_lat = loc["coordinates"][0], loc["coordinates"][1]
        else:
            handoff_lat = loc.get("lat", 0)
            handoff_lng = loc.get("lng", 0)
    
    # Set replacement drone to 'dispatching' status
    replacement_drone.status = "dispatching"
    replacement_drone.save()
    
    # Store replacement info in mission (for tracking)
    mission.pending_replacement_drone_id = replacement_drone.drone_id
    mission.handoff_location = {"type": "Point", "coordinates": [handoff_lng, handoff_lat]}
    mission.save()
    
    # Log replacement dispatch
    try:
        from dsms.models import log_handoff
        log_handoff(
            mission=mission,
            handoff_type="replacement_dispatched",
            outgoing_drone=current_drone,
            incoming_drone=replacement_drone,
            base=base,
            waypoint_index=current_waypoint_index,
            reason=f"Low battery ({current_drone.battery_level}%), replacement dispatched"
        )
        print(f"[HANDOFF] Logged replacement_dispatched event")
    except Exception as e:
        print(f"[HANDOFF] Could not log dispatch: {e}")
    
    # Start replacement flight simulation (flies from base to handoff location)
    try:
        simulate_replacement_flight.delay(
            replacement_drone_id=replacement_drone.drone_id,
            mission_id=mission.mission_id,
            target_lat=handoff_lat,
            target_lng=handoff_lng
        )
        print(f"[HANDOFF] Dispatched {replacement_drone.drone_id} to rendezvous at ({handoff_lat}, {handoff_lng})")
    except Exception as e:
        print(f"[HANDOFF] Could not dispatch replacement: {e}")
        # Rollback
        replacement_drone.status = "available"
        replacement_drone.save()
        mission.pending_replacement_drone_id = None
        mission.handoff_location = None
        mission.save()
        return None
    
    # Broadcast replacement_dispatched event via WebSocket
    if channel_layer:
        try:
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    "type": "replacement_dispatched",
                    "data": {
                        "mission_id": mission.mission_id,
                        "current_drone_id": current_drone.drone_id,
                        "current_battery": current_drone.battery_level,
                        "replacement_drone_id": replacement_drone.drone_id,
                        "replacement_battery": replacement_drone.battery_level,
                        "waypoint_index": current_waypoint_index,
                        "base_id": base_id,
                        "base_name": base.name if base else None,
                        "message": f"Replacement {replacement_drone.drone_id} dispatched to rendezvous",
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                },
            )
        except Exception as e:
            print(f"[HANDOFF] WebSocket broadcast error: {e}")
    
    return replacement_drone


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

            # Update mission progress and check phase transition
            mission.progress = result["progress"]
            mission.current_waypoint_index = result["current_waypoint"]
            
            # Check for phase transition (traveling -> surveying)
            if mission.mission_phase == "traveling" and simulator.is_surveying():
                mission.mission_phase = "surveying"
                print(f"[PHASE] Mission {mission_id}: Traveling → Surveying (waypoint {result['current_waypoint']})")
                
                # Broadcast phase change
                try:
                    async_to_sync(channel_layer.group_send)(
                        room_group_name,
                        {
                            "type": "phase_change",
                            "data": {
                                "mission_id": mission_id,
                                "old_phase": "traveling",
                                "new_phase": "surveying",
                                "message": "Drone arrived at survey area, beginning coverage pattern",
                                "timestamp": datetime.utcnow().isoformat(),
                            },
                        },
                    )
                except Exception:
                    pass
                    
            # Check if replacement drone has arrived (within 10m)
            if mission.pending_replacement_drone_id:
                try:
                    from dsms.models import Drone
                    from dsms.services.path_generator import haversine_distance
                    
                    # Get current mission drone
                    current_drone = Drone.objects.get(drone_id=mission.assigned_drone_id)
                    replacement_drone = Drone.objects.get(drone_id=mission.pending_replacement_drone_id)
                    
                    # Get positions
                    current_pos = current_drone.location
                    replacement_pos = replacement_drone.location
                    
                    if current_pos and replacement_pos:
                        # Extract coordinates
                        if "coordinates" in current_pos:
                            current_lng, current_lat = current_pos["coordinates"][0], current_pos["coordinates"][1]
                        else:
                            current_lat = current_pos.get("lat", 0)
                            current_lng = current_pos.get("lng", 0)
                        
                        if "coordinates" in replacement_pos:
                            repl_lng, repl_lat = replacement_pos["coordinates"][0], replacement_pos["coordinates"][1]
                        else:
                            repl_lat = replacement_pos.get("lat", 0)
                            repl_lng = replacement_pos.get("lng", 0)
                        
                        # Calculate distance
                        distance = haversine_distance(current_lat, current_lng, repl_lat, repl_lng)
                        
                        print(f"[RENDEZVOUS] Distance between {current_drone.drone_id} and {replacement_drone.drone_id}: {distance:.1f}m")
                        
                        if distance <= 10:
                            # Replacement has arrived! Trigger handoff completion
                            print(f"[RENDEZVOUS] Replacement within 10m! Triggering handoff...")
                            complete_handoff(mission_id, mission.pending_replacement_drone_id)
                            
                            # Reinitialize simulator with new drone
                            mission.reload()
                            simulator = DroneSimulator(mission)
                            simulator.current_waypoint = result["current_waypoint"]
                            simulator.battery = replacement_drone.battery_level
                            print(f"[RENDEZVOUS] Handoff complete, continuing with {replacement_drone.drone_id}")
                            
                except Exception as e:
                    print(f"[RENDEZVOUS] Error checking replacement arrival: {e}")
                    
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

            # Check for battery handoff
            if result["battery"] <= CRITICAL_BATTERY_LEVEL:
                from dsms.models import Drone
                current_drone = Drone.objects.get(drone_id=mission.assigned_drone_id)
                replacement = perform_battery_handoff(
                    mission,
                    current_drone,
                    result["current_waypoint"],
                    channel_layer
                )
                if replacement:
                    # Reinitialize simulator with new drone's battery
                    mission.reload()
                    simulator = DroneSimulator(mission)
                    # Set simulator state to continue from current waypoint
                    simulator.current_waypoint = result["current_waypoint"]
                    simulator.battery = replacement.battery_level
                    print(f"[HANDOFF] Continuing mission with {replacement.drone_id}")

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
                
                # Check for phase transition (traveling -> surveying)
                if mission.mission_phase == "traveling" and simulator.is_surveying():
                    mission.mission_phase = "surveying"
                    mission.save()
                    print(f"[SYNC PHASE] Mission {mission_id}: Traveling → Surveying")
                    
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

            # Check for battery handoff
            if result["battery"] <= CRITICAL_BATTERY_LEVEL:
                from dsms.models import Drone
                try:
                    current_drone = Drone.objects.get(drone_id=mission.assigned_drone_id)
                    replacement = perform_battery_handoff(
                        mission,
                        current_drone,
                        result["current_waypoint"],
                        None  # No channel layer in sync mode
                    )
                    if replacement:
                        # Reinitialize simulator with new drone's battery
                        mission.reload()
                        simulator = DroneSimulator(mission)
                        simulator.current_waypoint = result["current_waypoint"]
                        simulator.battery = replacement.battery_level
                        print(f"[SYNC HANDOFF] Continuing mission with {replacement.drone_id}")
                except Exception as e:
                    print(f"[SYNC] Handoff error: {e}")

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


@shared_task(bind=True)
def simulate_return_flight(self, drone_id: str, base_id: str = None, current_position: list = None):
    """
    Simulate a drone returning to its base after being replaced.
    Updates drone location along the return path, then starts charging.
    
    Args:
        drone_id: ID of the returning drone
        base_id: ID of the destination base
        current_position: Current [lng, lat] position (GeoJSON format)
    """
    from dsms.models import Drone
    from dsms.services import base_service
    
    print(f"[RETURN] Starting return flight for drone {drone_id} to base {base_id}")
    
    try:
        drone = Drone.objects.get(drone_id=drone_id)
    except Drone.DoesNotExist:
        print(f"[RETURN] Drone {drone_id} not found")
        return {"status": "error", "reason": "drone_not_found"}
    
    # Get base location
    base_lat, base_lng = 0.0, 0.0
    if base_id:
        try:
            base = base_service.get_base(base_id)
            base_lat, base_lng = base.lat, base.lng
        except Exception:
            pass
    elif drone.home_base:
        base_lat = drone.home_base.get("lat", 0)
        base_lng = drone.home_base.get("lng", 0)
    
    # Get current position
    if current_position and len(current_position) >= 2:
        current_lng, current_lat = current_position[0], current_position[1]
    elif drone.location:
        loc = drone.location
        if "coordinates" in loc:
            current_lng, current_lat = loc["coordinates"][0], loc["coordinates"][1]
        else:
            current_lat = loc.get("lat", 0)
            current_lng = loc.get("lng", 0)
    else:
        current_lng, current_lat = 0, 0
    
    # Calculate return path (simple direct flight)
    from dsms.services.path_generator import haversine_distance
    distance = haversine_distance(current_lat, current_lng, base_lat, base_lng)
    
    # Assume 10 m/s return speed, simulate travel
    travel_time = int(distance / 10) if distance > 0 else 5
    travel_time = min(travel_time, 30)  # Cap at 30 seconds for demo
    travel_time = max(travel_time, 5)   # Minimum 5 seconds
    
    print(f"[RETURN] Drone {drone_id} returning to base, ETA: {travel_time}s, distance: {distance:.0f}m")
    
    # Simulate return flight with position updates
    for tick in range(travel_time):
        try:
            drone = Drone.objects.get(drone_id=drone_id)
            
            if drone.status != "returning":
                print(f"[RETURN] Drone {drone_id} status changed, stopping return simulation")
                return {"status": "interrupted", "reason": drone.status}
            
            # Interpolate position
            progress = (tick + 1) / travel_time
            new_lat = current_lat + progress * (base_lat - current_lat)
            new_lng = current_lng + progress * (base_lng - current_lng)
            
            # Update drone location
            drone.location = {"type": "Point", "coordinates": [new_lng, new_lat]}
            drone.save()
            
            print(f"[RETURN] Drone {drone_id}: {progress*100:.0f}% to base")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"[RETURN] Error: {e}")
            break
    
    # Arrived at base - update location to exactly base position and start charging
    try:
        drone = Drone.objects.get(drone_id=drone_id)
        drone.location = {"type": "Point", "coordinates": [base_lng, base_lat]}
        drone.status = "charging"
        drone.save()
        
        print(f"[RETURN] Drone {drone_id} arrived at base, starting charging")
        
        # Log return to base event
        try:
            from dsms.models import log_handoff, DroneHandoffLog
            
            # Create a simple log entry for return
            log = DroneHandoffLog(
                mission_id="return_flight",
                handoff_type="return_to_base",
                outgoing_drone_id=drone_id,
                outgoing_drone_battery=drone.battery_level,
                base_id=base_id,
                reason="Low battery return"
            )
            log.save()
        except Exception as e:
            print(f"[RETURN] Could not log return: {e}")
        
        # Start charging
        charge_drone_task.delay(drone_id)
        
    except Exception as e:
        print(f"[RETURN] Could not complete return: {e}")
        return {"status": "error", "reason": str(e)}
    
    return {"status": "complete", "drone_id": drone_id, "base_id": base_id}


@shared_task(bind=True)
def simulate_replacement_flight(
    self,
    replacement_drone_id: str,
    mission_id: str,
    target_lat: float,
    target_lng: float
):
    """
    Simulate replacement drone flying from base to rendezvous point.
    Uses generated flight path - NO TELEPORTATION!
    
    When replacement gets within 10m of target, triggers handoff completion.
    
    Args:
        replacement_drone_id: ID of the replacement drone
        mission_id: ID of the mission needing help
        target_lat, target_lng: Where to fly to (handoff location)
    """
    from dsms.models import Drone, Mission
    from dsms.services import base_service, path_generator
    
    print(f"[REPLACEMENT] Starting dispatch for {replacement_drone_id} to mission {mission_id}")
    
    try:
        drone = Drone.objects.get(drone_id=replacement_drone_id)
        mission = Mission.objects.get(mission_id=mission_id)
    except (Drone.DoesNotExist, Mission.DoesNotExist) as e:
        print(f"[REPLACEMENT] Not found: {e}")
        return {"status": "error", "reason": str(e)}
    
    # Get drone's base location
    base_lat, base_lng = 0.0, 0.0
    if drone.base_id:
        try:
            base = base_service.get_base(drone.base_id)
            base_lat, base_lng = base.lat, base.lng
        except Exception:
            pass
    elif drone.home_base:
        base_lat = drone.home_base.get("lat", 0)
        base_lng = drone.home_base.get("lng", 0)
    
    # Generate flight path from base to handoff location
    try:
        waypoints = path_generator.generate_travel_path(
            start_lat=base_lat,
            start_lng=base_lng,
            end_lat=target_lat,
            end_lng=target_lng,
            altitude=mission.altitude or 50.0
        )
        print(f"[REPLACEMENT] Generated path with {len(waypoints)} waypoints")
    except Exception as e:
        print(f"[REPLACEMENT] Could not generate path: {e}")
        # Fallback: direct interpolation
        waypoints = []
    
    # Calculate total distance
    distance = path_generator.haversine_distance(base_lat, base_lng, target_lat, target_lng)
    
    # Simulate flight along waypoints
    if waypoints:
        # Fly through each waypoint
        for i, wp in enumerate(waypoints):
            try:
                drone = Drone.objects.get(drone_id=replacement_drone_id)
                
                # Check if mission still needs replacement
                mission.reload()
                if not mission.pending_replacement_drone_id or mission.status not in ["in_progress", "paused"]:
                    print(f"[REPLACEMENT] Mission no longer needs replacement, aborting dispatch")
                    drone.status = "available"
                    drone.save()
                    return {"status": "cancelled", "reason": "mission_changed"}
                
                if drone.status != "dispatching":
                    print(f"[REPLACEMENT] Drone status changed, stopping dispatch")
                    return {"status": "interrupted", "reason": drone.status}
                
                # Update drone position to this waypoint
                drone.location = {"type": "Point", "coordinates": [wp.lng, wp.lat]}
                drone.save()
                
                print(f"[REPLACEMENT] Waypoint {i+1}/{len(waypoints)}, dist to target: {path_generator.haversine_distance(wp.lat, wp.lng, target_lat, target_lng):.0f}m")
                
                # Check distance to target
                dist_to_target = path_generator.haversine_distance(wp.lat, wp.lng, target_lat, target_lng)
                
                if dist_to_target <= 10:
                    # Within 10m - trigger handoff!
                    print(f"[REPLACEMENT] Within 10m of target! Triggering handoff completion...")
                    complete_handoff(mission_id, replacement_drone_id)
                    return {"status": "handoff_triggered", "distance": dist_to_target}
                
                time.sleep(1)  # Update every second
                
            except Exception as e:
                print(f"[REPLACEMENT] Error during flight: {e}")
                break
    else:
        # Fallback: simple interpolation
        travel_time = int(distance / 10) if distance > 0 else 5
        travel_time = min(travel_time, 60)  # Cap at 60 seconds
        
        for tick in range(travel_time):
            try:
                drone = Drone.objects.get(drone_id=replacement_drone_id)
                mission.reload()
                
                if not mission.pending_replacement_drone_id or mission.status not in ["in_progress", "paused"]:
                    drone.status = "available"
                    drone.save()
                    return {"status": "cancelled"}
                
                if drone.status != "dispatching":
                    return {"status": "interrupted"}
                
                # Interpolate position
                progress = (tick + 1) / travel_time
                new_lat = base_lat + progress * (target_lat - base_lat)
                new_lng = base_lng + progress * (target_lng - target_lng)
                
                drone.location = {"type": "Point", "coordinates": [new_lng, new_lat]}
                drone.save()
                
                # Check distance
                dist_to_target = path_generator.haversine_distance(new_lat, new_lng, target_lat, target_lng)
                
                if dist_to_target <= 10:
                    complete_handoff(mission_id, replacement_drone_id)
                    return {"status": "handoff_triggered", "distance": dist_to_target}
                
                time.sleep(1)
                
            except Exception as e:
                print(f"[REPLACEMENT] Error: {e}")
                break
    
    # Should have triggered handoff by now
    print(f"[REPLACEMENT] Reached target area")
    complete_handoff(mission_id, replacement_drone_id)
    return {"status": "complete"}


def complete_handoff(mission_id: str, replacement_drone_id: str):
    """
    Complete the handoff when replacement drone reaches 10m proximity.
    This is called by simulate_replacement_flight when distance <= 10m.
    """
    from dsms.models import Drone, Mission, log_handoff
    from dsms.services import base_service
    
    try:
        mission = Mission.objects.get(mission_id=mission_id)
        replacement_drone = Drone.objects.get(drone_id=replacement_drone_id)
        outgoing_drone = Drone.objects.get(drone_id=mission.assigned_drone_id)
    except Exception as e:
        print(f"[HANDOFF_COMPLETE] Error loading data: {e}")
        return
    
    print(f"[HANDOFF_COMPLETE] Executing swap: {outgoing_drone.drone_id} → {replacement_drone.drone_id}")
    
    # Get base info
    base = None
    base_id = mission.origin_base_id or outgoing_drone.base_id
    if base_id:
        try:
            base = base_service.get_base(base_id)
        except Exception:
            pass
    
    # Log the completed handoff
    try:
        log_handoff(
            mission=mission,
            handoff_type="handoff_complete",
            outgoing_drone=outgoing_drone,
            incoming_drone=replacement_drone,
            base=base,
            waypoint_index=mission.current_waypoint_index,
            reason=f"Rendezvous complete (10m proximity)"
        )
    except Exception as e:
        print(f"[HANDOFF_COMPLETE] Could not log: {e}")
    
    # Outgoing drone returns to base
    outgoing_drone.status = "returning"
    outgoing_drone.current_mission_id = None
    outgoing_drone.save()
    
    # Start return flight
    try:
        simulate_return_flight.delay(
            outgoing_drone.drone_id,
            base_id,
            outgoing_drone.location.get("coordinates") if outgoing_drone.location else None
        )
        print(f"[HANDOFF_COMPLETE] {outgoing_drone.drone_id} returning to base")
    except Exception as e:
        print(f"[HANDOFF_COMPLETE] Could not start return flight: {e}")
    
    # Incoming drone takes over mission
    replacement_drone.status = "in_flight"
    replacement_drone.current_mission_id = mission.mission_id
    replacement_drone.save()
    
    # Update mission
    mission.assigned_drone_id = replacement_drone.drone_id
    mission.pending_replacement_drone_id = None
    mission.handoff_location = None
    mission.save()
    
    print(f"[HANDOFF_COMPLETE] Mission {mission_id} now assigned to {replacement_drone.drone_id}")
    
    # Broadcast handoff complete event
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"mission_{mission_id}",
            {
                "type": "handoff_complete",
                "data": {
                    "mission_id": mission_id,
                    "old_drone_id": outgoing_drone.drone_id,
                    "old_drone_battery": outgoing_drone.battery_level,
                    "new_drone_id": replacement_drone.drone_id,
                    "new_drone_battery": replacement_drone.battery_level,
                    "waypoint_index": mission.current_waypoint_index,
                    "base_id": base_id,
                    "base_name": base.name if base else None,
                    "message": f"Handoff complete: {outgoing_drone.drone_id} → {replacement_drone.drone_id}",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            },
        )
    except Exception as e:
        print(f"[HANDOFF_COMPLETE] WebSocket broadcast error: {e}")
