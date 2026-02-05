"""
Mission Service
Business logic for mission operations.
Sentry pattern: All mission-related logic centralized here.
"""

import math
from datetime import datetime
from typing import Any, Dict, List, Optional

from dsms.db import connect_db
from dsms.utils.exceptions import MissionError, NotFoundError, ValidationError

# Ensure DB connection
connect_db()

from dsms.models import Drone, FlightPath, Mission, Waypoint
from dsms.services import path_generator


def calculate_polygon_area(coordinates: List[List[float]]) -> float:
    """
    Calculate area of a polygon using the Shoelace formula.
    Coordinates should be in [lng, lat] format (GeoJSON).
    Returns area in square meters.
    """
    if not coordinates or len(coordinates) < 3:
        return 0.0

    # Convert coordinates to radians and calculate area using spherical excess
    # For simplicity, use planar approximation (good enough for small areas)
    area = 0.0
    n = len(coordinates)

    # Approximate conversion: 1 degree ≈ 111km at equator
    # Use average latitude for better accuracy
    avg_lat = sum(coord[1] for coord in coordinates) / n
    lat_to_meters = 111000.0
    lng_to_meters = 111000.0 * math.cos(math.radians(avg_lat))

    # Convert to meters
    coords_meters = [
        (coord[0] * lng_to_meters, coord[1] * lat_to_meters) for coord in coordinates
    ]

    # Shoelace formula
    for i in range(n):
        j = (i + 1) % n
        area += coords_meters[i][0] * coords_meters[j][1]
        area -= coords_meters[j][0] * coords_meters[i][1]

    area = abs(area) / 2.0
    return area


def get_mission_center(mission: Mission) -> tuple:
    """Get the center point of a mission's coverage area"""
    if not mission.coverage_area or "coordinates" not in mission.coverage_area:
        return None, None

    coords = mission.coverage_area["coordinates"][0]
    if not coords:
        return None, None

    # Calculate centroid
    lngs = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    center_lng = sum(lngs) / len(lngs)
    center_lat = sum(lats) / len(lats)

    return center_lat, center_lng


def auto_assign_drone(mission: Mission) -> Drone:
    """
    Automatically assign the best available drone to a mission.

    Algorithm:
    1. Find the nearest active base to the mission's coverage area
    2. Get available drones at that base
    3. Select the drone with the highest battery level
    4. Assign drone to mission

    Returns:
        Drone: The assigned drone

    Raises:
        ValidationError: If no drone is available
    """
    from dsms.services import base_service

    # Get mission center point
    center_lat, center_lng = get_mission_center(mission)

    if center_lat is None:
        # No coverage area - try to find any available drone
        available_drones = list(
            Drone.objects(status="available").order_by("-battery_level")
        )
        if not available_drones:
            raise ValidationError("No available drones in the fleet")

        best_drone = available_drones[0]
        print(
            f"[AUTO-ASSIGN] No coverage area, assigned {best_drone.drone_id} (battery: {best_drone.battery_level}%)"
        )
        return best_drone

    # Find nearest base
    nearest_base = base_service.find_nearest_base(center_lat, center_lng)

    if nearest_base:
        # Get available drones at nearest base, sorted by battery (highest first)
        base_drones = list(
            Drone.objects(base_id=nearest_base.base_id, status="available").order_by(
                "-battery_level"
            )
        )

        if base_drones:
            best_drone = base_drones[0]
            print(
                f"[AUTO-ASSIGN] Found drone {best_drone.drone_id} at base {nearest_base.name} (battery: {best_drone.battery_level}%)"
            )
            return best_drone
        else:
            print(
                f"[AUTO-ASSIGN] No available drones at nearest base {nearest_base.name}"
            )

    # Fallback: Find any available drone sorted by battery
    all_available = list(Drone.objects(status="available").order_by("-battery_level"))

    if not all_available:
        raise ValidationError(
            "No available drones. All drones are either in flight, charging, or in maintenance."
        )

    best_drone = all_available[0]
    print(
        f"[AUTO-ASSIGN] Fallback: assigned {best_drone.drone_id} (battery: {best_drone.battery_level}%)"
    )
    return best_drone


def get_mission(mission_id: str) -> Mission:
    """Get a mission by ID"""
    try:
        return Mission.objects.get(mission_id=mission_id)
    except Mission.DoesNotExist:
        raise NotFoundError(f"Mission '{mission_id}' not found")


def list_missions(filters: Optional[Dict[str, Any]] = None) -> List[Mission]:
    """List missions with optional filters"""
    queryset = Mission.objects

    if filters:
        if "status" in filters:
            queryset = queryset.filter(status=filters["status"])
        if "site" in filters or "site_name" in filters:
            site_name = filters.get("site_name") or filters.get("site")
            queryset = queryset.filter(site_name=site_name)
        if "drone_id" in filters or "assigned_drone_id" in filters:
            drone_id = filters.get("assigned_drone_id") or filters.get("drone_id")
            queryset = queryset.filter(assigned_drone_id=drone_id)

    return list(queryset.order_by("-created_at"))


def create_mission(data: Dict[str, Any]) -> Mission:
    """Create a new mission"""
    # Generate mission ID
    count = Mission.objects.count()
    mission_id = f"MSN-{count + 1:04d}"

    # Create mission - use correct field names matching Mission model
    mission = Mission(
        mission_id=mission_id,
        name=data["name"],
        description=data.get("description", ""),
        site_name=data.get("site_name") or data.get("site", ""),
        coverage_area=data.get("coverage_area") or data.get("survey_area"),
        altitude=data.get("altitude", 50.0),
        speed=data.get("speed", 10.0),
        overlap=data.get("overlap_percentage", 70.0) or data.get("overlap", 70.0),
        survey_type=data.get("survey_type", "mapping"),
        scheduled_start=data.get("scheduled_start"),
        assigned_drone_id=data.get("assigned_drone_id") or data.get("drone_id"),
    )

    # Assign drone if provided
    drone_id = data.get("assigned_drone_id") or data.get("drone_id")
    if drone_id:
        try:
            drone = Drone.objects.get(drone_id=drone_id)
            mission.assigned_drone_id = drone.drone_id
        except Drone.DoesNotExist:
            raise ValidationError(f"Drone '{drone_id}' not found")

    # Create flight path from waypoints if provided
    if "waypoints" in data and data["waypoints"]:
        waypoints = []
        for wp_data in data["waypoints"]:
            # Handle GeoJSON Point format {type: 'Point', coordinates: [lng, lat]}
            if "location" in wp_data and isinstance(wp_data["location"], dict):
                coords = wp_data["location"].get("coordinates", [])
                lng = coords[0] if len(coords) > 0 else 0.0
                lat = coords[1] if len(coords) > 1 else 0.0
            else:
                # Direct lat/lng
                lat = wp_data.get("lat", 0.0)
                lng = wp_data.get("lng", 0.0)

            waypoint = Waypoint(
                lat=lat,
                lng=lng,
                alt=wp_data.get("altitude") or wp_data.get("alt", mission.altitude),
                action=wp_data.get("action", "fly"),
                duration=wp_data.get("duration", 0.0),
            )
            waypoints.append(waypoint)

        # Get pattern type from data or default
        pattern_type = data.get("pattern_type", "waypoint")
        if pattern_type not in ["crosshatch", "perimeter", "spiral", "waypoint"]:
            pattern_type = "waypoint"

        flight_path = FlightPath(
            pattern_type=pattern_type,
            waypoints=waypoints,
        )
        # Calculate distance if path_generator supports it
        try:
            flight_path.total_distance = path_generator.calculate_path_distance(
                waypoints
            )
            flight_path.estimated_duration = (
                int(flight_path.total_distance / mission.speed)
                if mission.speed > 0
                else 0
            )
        except:
            # Fallback calculation
            flight_path.total_distance = 0.0
            flight_path.estimated_duration = 0
        mission.flight_path = flight_path

    mission.save()

    # Auto-generate flight path from coverage area if not already created
    if mission.coverage_area and (
        not mission.flight_path or not mission.flight_path.waypoints
    ):
        try:
            mission = generate_flight_path(mission.mission_id)
        except Exception as e:
            print(f"[WARNING] Could not generate flight path: {e}")

    return mission


def update_mission(mission_id: str, data: Dict[str, Any]) -> Mission:
    """Update an existing mission"""
    mission = get_mission(mission_id)

    if mission.status == "in_progress":
        raise MissionError("Cannot update mission while in progress")

    # Update allowed fields - use correct field names matching Mission model
    if "name" in data:
        mission.name = data["name"]
    if "description" in data:
        mission.description = data["description"]
    if "site_name" in data or "site" in data:
        mission.site_name = data.get("site_name") or data.get("site", "")
    if "coverage_area" in data or "survey_area" in data:
        mission.coverage_area = data.get("coverage_area") or data.get("survey_area")
    if "altitude" in data:
        mission.altitude = data["altitude"]
    if "speed" in data:
        mission.speed = data["speed"]
    if "overlap_percentage" in data or "overlap" in data:
        mission.overlap = data.get("overlap_percentage") or data.get("overlap", 70.0)
    if "survey_type" in data:
        mission.survey_type = data["survey_type"]
    if "scheduled_start" in data:
        mission.scheduled_start = data["scheduled_start"]

    # Handle drone assignment
    drone_id = data.get("assigned_drone_id") or data.get("drone_id")
    if drone_id is not None:
        if drone_id:
            try:
                drone = Drone.objects.get(drone_id=drone_id)
                mission.assigned_drone_id = drone.drone_id
            except Drone.DoesNotExist:
                raise ValidationError(f"Drone '{drone_id}' not found")
        else:
            mission.assigned_drone_id = None

    mission.save()
    return mission


def delete_mission(mission_id: str) -> None:
    """Delete a mission"""
    mission = get_mission(mission_id)

    if mission.status == "in_progress":
        raise MissionError("Cannot delete mission while in progress")

    mission.delete()


def start_mission(mission_id: str) -> Mission:
    """Start a mission execution with automatic drone assignment"""
    mission = get_mission(mission_id)

    if mission.status not in ["draft", "scheduled"]:
        raise MissionError(f"Cannot start mission with status '{mission.status}'")

    # Auto-assign drone if not already assigned
    if not mission.assigned_drone_id:
        print(f"[START_MISSION] No drone assigned, auto-assigning...")
        drone = auto_assign_drone(mission)
        mission.assigned_drone_id = drone.drone_id
        mission.save()
        print(f"[START_MISSION] Auto-assigned drone {drone.drone_id}")
    else:
        # Verify assigned drone exists and is available
        try:
            drone = Drone.objects.get(drone_id=mission.assigned_drone_id)
        except Drone.DoesNotExist:
            raise ValidationError(
                f"Assigned drone '{mission.assigned_drone_id}' not found"
            )

        if drone.status != "available":
            # Try to auto-assign a different drone
            print(f"[START_MISSION] Assigned drone not available, reassigning...")
            drone = auto_assign_drone(mission)
            mission.assigned_drone_id = drone.drone_id
            mission.save()
            print(f"[START_MISSION] Reassigned to drone {drone.drone_id}")

    # Auto-generate flight path if missing
    if not mission.flight_path or not mission.flight_path.waypoints:
        if mission.coverage_area:
            try:
                mission = generate_flight_path(mission.mission_id)
            except Exception as e:
                raise ValidationError(f"Could not generate flight path: {str(e)}")
        else:
            raise ValidationError(
                "Mission has no coverage area and no flight path defined"
            )

    # Get the drone again (in case it was auto-assigned)
    drone = Drone.objects.get(drone_id=mission.assigned_drone_id)

    if drone.status != "available":
        raise MissionError(
            f"Drone '{drone.drone_id}' is not available (status: {drone.status})"
        )

    # Store origin base for handoff
    mission.origin_base_id = drone.base_id

    # Generate travel path from base to mission start
    if drone.base_id and mission.flight_path and mission.flight_path.waypoints:
        from dsms.services import base_service
        from dsms.utils.geo import normalize_longitude

        try:
            base = base_service.get_base(drone.base_id)
            first_waypoint = mission.flight_path.waypoints[0]

            # Normalize waypoint longitude to handle Leaflet map wrapping
            # (e.g., -282 degrees should be normalized to 77 degrees)
            normalized_end_lng = normalize_longitude(first_waypoint.lng)

            # Generate travel waypoints from base to first survey waypoint
            travel_waypoints = path_generator.generate_travel_path(
                start_lat=base.lat,
                start_lng=base.lng,
                end_lat=first_waypoint.lat,
                end_lng=normalized_end_lng,
                altitude=mission.altitude,
            )

            # Normalize ALL existing waypoints to fix any with invalid coordinates
            # This handles missions created before the normalization fix
            normalized_existing_waypoints = []
            for wp in mission.flight_path.waypoints:
                normalized_lng = normalize_longitude(wp.lng)
                from dsms.models import Waypoint as WaypointModel

                normalized_wp = WaypointModel(
                    lat=wp.lat,
                    lng=normalized_lng,
                    alt=wp.alt,
                    action=wp.action,
                    duration=wp.duration,
                )
                normalized_existing_waypoints.append(normalized_wp)

            # Prepend travel waypoints to the normalized mission path
            if travel_waypoints:
                all_waypoints = travel_waypoints + normalized_existing_waypoints
                mission.flight_path.waypoints = all_waypoints

                # Recalculate total distance
                mission.flight_path.total_distance = (
                    path_generator.calculate_path_distance(all_waypoints)
                )
                mission.flight_path.estimated_duration = (
                    int(mission.flight_path.total_distance / mission.speed)
                    if mission.speed > 0
                    else 0
                )

                print(
                    f"[START_MISSION] Added {len(travel_waypoints)} travel waypoints from base {base.name}"
                )

            # Generate return path from last survey waypoint back to base
            if mission.flight_path and mission.flight_path.waypoints:
                last_waypoint = mission.flight_path.waypoints[-1]
                normalized_start_lng = normalize_longitude(last_waypoint.lng)

                # Generate return waypoints from last survey waypoint to base
                return_waypoints = path_generator.generate_travel_path(
                    start_lat=last_waypoint.lat,
                    start_lng=normalized_start_lng,
                    end_lat=base.lat,
                    end_lng=base.lng,
                    altitude=mission.altitude,
                    action="fly",  # Use valid action type
                )

                if return_waypoints:
                    # Append return waypoints to the mission path
                    mission.flight_path.waypoints = (
                        list(mission.flight_path.waypoints) + return_waypoints
                    )

                    # Recalculate total distance including return path
                    mission.flight_path.total_distance = (
                        path_generator.calculate_path_distance(
                            mission.flight_path.waypoints
                        )
                    )
                    mission.flight_path.estimated_duration = (
                        int(mission.flight_path.total_distance / mission.speed)
                        if mission.speed > 0
                        else 0
                    )

                    print(
                        f"[START_MISSION] Added {len(return_waypoints)} return waypoints to base {base.name}"
                    )

        except Exception as e:
            print(f"[START_MISSION] Could not add travel/return path: {e}")
            # Continue without travel path - not critical

    # Update drone status
    drone.status = "in_flight"
    drone.current_mission_id = mission.mission_id
    drone.save()

    # Update mission status
    mission.status = "in_progress"
    mission.mission_phase = "traveling"  # Start in traveling phase
    mission.started_at = datetime.utcnow()
    mission.progress = 0.0
    mission.current_waypoint_index = 0
    mission.save()

    # Log mission start (initial drone assignment)
    try:
        from dsms.models import log_handoff
        from dsms.services import base_service

        base = None
        if mission.origin_base_id:
            try:
                base = base_service.get_base(mission.origin_base_id)
            except Exception:
                pass

        log_handoff(
            mission=mission,
            handoff_type="start",
            incoming_drone=drone,
            base=base,
            waypoint_index=0,
            reason="Mission started",
        )
        print(
            f"[START_MISSION] Logged initial drone assignment for {mission.mission_id}"
        )
    except Exception as e:
        print(f"[START_MISSION] Could not log start event: {e}")

    # Start simulation - try async first, fallback to thread
    try:
        from dsms.tasks.simulator import run_mission_simulation

        run_mission_simulation.delay(mission_id)
        print(f"[INFO] Started async simulation for mission {mission_id}")
    except Exception as e:
        # Celery not available - run in background thread
        print(f"[INFO] Celery not available, starting threaded simulation: {e}")
        import threading

        from dsms.tasks.simulator import run_mission_simulation_sync

        thread = threading.Thread(
            target=run_mission_simulation_sync, args=(mission_id,), daemon=True
        )
        thread.start()
        print(f"[INFO] Started threaded simulation for mission {mission_id}")

    return mission


def pause_mission(mission_id: str) -> Mission:
    """Pause a running mission"""
    mission = get_mission(mission_id)

    if mission.status != "in_progress":
        raise MissionError("Mission is not in progress")

    mission.status = "paused"
    mission.save()
    return mission


def resume_mission(mission_id: str) -> Mission:
    """Resume a paused mission"""
    mission = get_mission(mission_id)

    if mission.status != "paused":
        raise MissionError("Mission is not paused")

    mission.status = "in_progress"
    mission.save()

    # Resume simulation
    try:
        from dsms.tasks.simulator import run_mission_simulation

        run_mission_simulation.delay(mission_id)
    except Exception:
        pass

    return mission


def abort_mission(mission_id: str) -> Mission:
    """Abort a mission"""
    mission = get_mission(mission_id)

    if mission.status not in ["in_progress", "paused"]:
        raise MissionError("Mission cannot be aborted")

    mission.status = "aborted"
    mission.completed_at = datetime.utcnow()
    mission.save()

    # Release drone
    if mission.assigned_drone_id:
        try:
            drone = Drone.objects.get(drone_id=mission.assigned_drone_id)
            drone.status = "available"
            drone.current_mission_id = None
            drone.save()
        except Drone.DoesNotExist:
            pass

    return mission


def complete_mission(mission_id: str) -> Mission:
    """Mark mission as completed (called by simulator)"""
    mission = get_mission(mission_id)

    mission.status = "completed"
    mission.progress = 100.0
    mission.completed_at = datetime.utcnow()

    # Calculate area covered if coverage_area exists
    if mission.coverage_area and mission.coverage_area.get("coordinates"):
        try:
            coords = mission.coverage_area["coordinates"][0]  # Get outer ring
            area = calculate_polygon_area(coords)
            mission.area_covered = area
        except Exception as e:
            print(f"[WARNING] Could not calculate area covered: {e}")

    mission.save()

    # Set drone to charging (not available until fully charged)
    if mission.assigned_drone_id:
        try:
            drone = Drone.objects.get(drone_id=mission.assigned_drone_id)
            drone.status = "charging"
            drone.current_mission_id = None
            drone.save()
            print(
                f"[INFO] Drone {drone.drone_id} started charging (battery: {drone.battery_level}%)"
            )

            # Start charging task - try Celery first, fallback to sync
            try:
                from dsms.tasks.simulator import charge_drone_task

                charge_drone_task.delay(drone.drone_id)
                print(f"[INFO] Started Celery charging task for drone {drone.drone_id}")
            except Exception as e:
                print(f"[INFO] Celery not available, using sync charging: {e}")
                from dsms.tasks.simulator import charge_drone_sync

                charge_drone_sync(drone.drone_id)
        except Drone.DoesNotExist:
            pass

    return mission


# Legacy function kept for backwards compatibility
def start_drone_charging(drone_id: str) -> None:
    """Start background charging for a drone - now uses Celery task"""
    try:
        from dsms.tasks.simulator import charge_drone_task

        charge_drone_task.delay(drone_id)
    except Exception:
        from dsms.tasks.simulator import charge_drone_sync

        charge_drone_sync(drone_id)


def generate_flight_path(mission_id: str) -> Mission:
    """Auto-generate flight path based on survey area and pattern"""
    mission = get_mission(mission_id)

    if not mission.coverage_area:
        raise ValidationError("Mission has no coverage area defined")

    # Get pattern type from flight_path if exists, otherwise default to crosshatch for full coverage
    pattern_type = "crosshatch"
    if mission.flight_path and mission.flight_path.pattern_type:
        pattern_type = mission.flight_path.pattern_type

    # Generate path based on pattern type
    flight_path = path_generator.generate_path(
        survey_area=mission.coverage_area,
        pattern=pattern_type,
        altitude=mission.altitude,
        overlap=mission.overlap,
        speed=mission.speed,
    )

    mission.flight_path = flight_path
    mission.save()
    return mission
