"""
Simple Simulator Endpoint
For development/testing without Celery.
"""

import threading
import time
from datetime import datetime

from dsms.api.bases import BaseEndpoint
from dsms.db import connect_db
from dsms.services import fleet_service, mission_service, telemetry_service
from dsms.simulator.engine import DroneSimulator

connect_db()
from dsms.models import Mission


class SimulatorStartEndpoint(BaseEndpoint):
    """Start simulator for a mission (dev mode without Celery)"""

    def post(self, request, mission_id):
        """Start simulating a mission in a background thread"""
        try:
            mission = mission_service.get_mission(mission_id)
        except Exception as e:
            return self.respond_error(str(e), status=404)

        if mission.status != "in_progress":
            return self.respond_error(
                "Mission must be in progress to simulate", status=400
            )

        # Start simulator in background thread
        thread = threading.Thread(
            target=self._run_simulation, args=(mission_id,), daemon=True
        )
        thread.start()

        return self.respond({"message": "Simulator started", "mission_id": mission_id})

    def _run_simulation(self, mission_id: str):
        """Run simulation in background thread"""
        print(f"[SIMULATOR] Starting for mission {mission_id}")

        try:
            mission = Mission.objects.get(mission_id=mission_id)

            if not mission.assigned_drone_id:
                print(f"[SIMULATOR] No drone assigned to mission {mission_id}")
                return

            simulator = DroneSimulator(mission)
            tick_interval = 1.0  # seconds

            while True:
                # Reload mission to check status
                mission.reload()

                if mission.status not in ["in_progress", "paused"]:
                    print(
                        f"[SIMULATOR] Mission {mission_id} stopped (status: {mission.status})"
                    )
                    break

                if mission.status == "paused":
                    time.sleep(tick_interval)
                    continue

                # Run simulation tick
                result = simulator.tick(tick_interval)

                # Record telemetry
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

                try:
                    telemetry_service.record_telemetry(telemetry_data)
                except Exception as e:
                    print(f"[SIMULATOR] Telemetry error: {e}")

                # Update mission progress
                mission.progress = result["progress"]
                mission.current_waypoint_index = result["current_waypoint"]
                mission.save()

                # Update drone location and battery
                try:
                    fleet_service.update_drone_location(
                        mission.assigned_drone_id,
                        telemetry_data["location"],
                        result["battery"],
                    )
                except Exception as e:
                    print(f"[SIMULATOR] Drone update error: {e}")

                # Check if complete
                if result.get("complete"):
                    print(f"[SIMULATOR] Mission {mission_id} completed!")
                    try:
                        mission_service.complete_mission(mission_id)
                    except Exception as e:
                        print(f"[SIMULATOR] Complete mission error: {e}")
                    break

                # Sleep before next tick
                time.sleep(tick_interval)

        except Exception as e:
            print(f"[SIMULATOR] Error in simulation: {e}")
            import traceback

            traceback.print_exc()
