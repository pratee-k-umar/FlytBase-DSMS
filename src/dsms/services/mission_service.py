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
    """Start a mission execution"""
    mission = get_mission(mission_id)

    if mission.status not in ["draft", "scheduled"]:
        raise MissionError(f"Cannot start mission with status '{mission.status}'")

    if not mission.assigned_drone_id:
        raise ValidationError("Mission has no drone assigned")

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

    # Get and check drone availability
    try:
        drone = Drone.objects.get(drone_id=mission.assigned_drone_id)
    except Drone.DoesNotExist:
        raise ValidationError(f"Assigned drone '{mission.assigned_drone_id}' not found")

    if drone.status != "available":
        raise MissionError(
            f"Drone '{drone.drone_id}' is not available (status: {drone.status})"
        )

    # Update drone status
    drone.status = "in_flight"
    drone.current_mission_id = mission.mission_id
    drone.save()

    # Update mission status
    mission.status = "in_progress"
    mission.started_at = datetime.utcnow()
    mission.progress = 0.0
    mission.current_waypoint_index = 0
    mission.save()

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
            print(f"[INFO] Drone {drone.drone_id} started charging (battery: {drone.battery_level}%)")
            
            # Start charging task in background
            start_drone_charging(drone.drone_id)
        except Drone.DoesNotExist:
            pass

    return mission


def start_drone_charging(drone_id: str) -> None:
    """Start background charging for a drone"""
    import threading
    
    def charge_drone():
        """Charge drone to 100% in background"""
        import time
        
        CHARGE_RATE = 5.0  # % per second (fast for demo)
        
        while True:
            try:
                drone = Drone.objects.get(drone_id=drone_id)
                
                if drone.battery_level >= 100:
                    # Fully charged - set to available
                    drone.status = "available"
                    drone.battery_level = 100.0
                    drone.save()
                    print(f"[INFO] Drone {drone_id} fully charged and available")
                    break
                    
                if drone.status != "charging":
                    # Drone status changed externally, stop charging
                    print(f"[INFO] Drone {drone_id} charging interrupted (status: {drone.status})")
                    break
                
                # Charge battery
                new_level = min(100, drone.battery_level + CHARGE_RATE)
                drone.battery_level = new_level
                drone.save()
                print(f"[CHARGING] Drone {drone_id}: {new_level:.1f}%")
                
                time.sleep(1)  # Update every second
                
            except Drone.DoesNotExist:
                print(f"[WARNING] Drone {drone_id} not found during charging")
                break
            except Exception as e:
                print(f"[ERROR] Charging error for {drone_id}: {e}")
                break
    
    thread = threading.Thread(target=charge_drone, daemon=True)
    thread.start()


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
