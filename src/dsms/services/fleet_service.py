"""
Fleet Service
Business logic for drone fleet management.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from dsms.db import connect_db
from dsms.utils.exceptions import NotFoundError, ValidationError

# Ensure DB connection
connect_db()

from dsms.models import Drone


def get_drone(drone_id: str) -> Drone:
    """Get a drone by ID"""
    try:
        return Drone.objects.get(drone_id=drone_id)
    except Drone.DoesNotExist:
        raise NotFoundError(f"Drone '{drone_id}' not found")


def list_drones(filters: Optional[Dict[str, Any]] = None) -> List[Drone]:
    """List drones with optional filters"""
    queryset = Drone.objects

    if filters:
        if "status" in filters:
            queryset = queryset.filter(status=filters["status"])
        if "site" in filters:
            queryset = queryset.filter(site=filters["site"])

    return list(queryset.order_by("drone_id"))


def create_drone(data: Dict[str, Any]) -> Drone:
    """Register a new drone"""
    # Generate drone ID
    count = Drone.objects.count()
    drone_id = f"DRN-{count + 1:04d}"

    drone = Drone(
        drone_id=drone_id,
        name=data["name"],
        model=data.get("model", ""),
        manufacturer=data.get("manufacturer", ""),
        base_id=data.get("base_id", ""),
        assigned_site=data.get("assigned_site", ""),
        max_flight_time=data.get("max_flight_time", 30),
        max_speed=data.get("max_speed", 15.0),
        max_altitude=data.get("max_altitude", 120.0),
        payload_capacity=data.get("payload_capacity", 0.5),
        status="available",
        battery_level=100,
    )

    drone.save()
    return drone


def update_drone(drone_id: str, data: Dict[str, Any]) -> Drone:
    """Update a drone"""
    drone = get_drone(drone_id)

    # Can't update drone that's in a mission (except battery/location)
    if drone.status == "in_mission":
        allowed_fields = ["battery_level", "location"]
        for key in list(data.keys()):
            if key not in allowed_fields:
                raise ValidationError(
                    f"Cannot update '{key}' while drone is in mission"
                )

    # Update allowed fields
    allowed_fields = [
        "name",
        "model",
        "manufacturer",
        "assigned_site",
        "status",
        "battery_level",
        "max_flight_time",
        "max_speed",
        "max_altitude",
        "payload_capacity",
        "location",
        "base_id",
    ]

    for field in allowed_fields:
        if field in data:
            setattr(drone, field, data[field])

    drone.save()
    return drone


def delete_drone(drone_id: str) -> None:
    """Delete a drone"""
    drone = get_drone(drone_id)

    # Can't delete drone that's currently in use
    if drone.status in ["in_flight", "dispatching", "returning"]:
        raise ValidationError(
            f"Cannot delete drone '{drone_id}' while it is {drone.status}"
        )

    # Can't delete if assigned to active mission
    if drone.current_mission_id:
        from dsms.models import Mission

        try:
            mission = Mission.objects.get(mission_id=drone.current_mission_id)
            if mission.status in ["in_progress", "paused"]:
                raise ValidationError(
                    f"Cannot delete drone '{drone_id}' - assigned to active mission '{mission.mission_id}'"
                )
        except Mission.DoesNotExist:
            pass  # Mission doesn't exist, safe to delete

    drone.delete()


def update_drone_location(
    drone_id: str, location: Dict, battery_level: int = None
) -> Drone:
    """Update drone location (called by telemetry)"""
    drone = get_drone(drone_id)

    drone.last_location = location
    drone.last_seen = datetime.utcnow()

    if battery_level is not None:
        drone.battery_level = battery_level

    drone.save()
    return drone


def get_fleet_stats() -> Dict[str, Any]:
    """Get fleet-wide statistics"""
    total = Drone.objects.count()

    # Count by status
    available = Drone.objects.filter(status="available").count()
    in_mission = Drone.objects.filter(status="in_mission").count()
    charging = Drone.objects.filter(status="charging").count()
    maintenance = Drone.objects.filter(status="maintenance").count()
    offline = Drone.objects.filter(status="offline").count()
    in_flight = Drone.objects.filter(status="in_flight").count()

    # Average battery level
    drones = list(Drone.objects.all())
    avg_battery = sum(d.battery_level for d in drones) / total if total > 0 else 0

    # Low battery count (< 20%)
    low_battery = len([d for d in drones if d.battery_level < 20])

    return {
        "total": total,
        "available": available,
        "in_mission": in_mission + in_flight,  # Combine in_mission and in_flight
        "charging": charging,
        "maintenance": maintenance,
        "offline": offline,
        "average_battery": round(avg_battery, 1),
        "low_battery": low_battery,
    }


def fix_stale_drone_statuses():
    """
    Fix drones that have stale statuses.
    Resets drones to 'available' if they are marked as in_flight/in_mission
    but are not actually assigned to any active mission.
    """
    from dsms.models import Mission

    # Get all missions that are active
    active_missions = Mission.objects.filter(status__in=["in_progress", "paused"])
    active_drone_ids = {
        m.assigned_drone_id for m in active_missions if m.assigned_drone_id
    }

    # Find drones that are marked as busy but not in active missions
    stale_drones = Drone.objects.filter(status__in=["in_flight", "in_mission"])

    fixed_count = 0
    for drone in stale_drones:
        if drone.drone_id not in active_drone_ids:
            print(f"[FIX] Resetting {drone.drone_id} from {drone.status} to available")
            drone.status = "available"
            drone.current_mission_id = None
            drone.save()
            fixed_count += 1

    return fixed_count
