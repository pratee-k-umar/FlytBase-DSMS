"""
DroneHandoffLog Model
Records all drone handoff events during missions for analytics.
"""

from datetime import datetime
from mongoengine import (
    StringField, FloatField, IntField, DictField, DateTimeField
)
from dsms.models.base import BaseDocument


class DroneHandoffLog(BaseDocument):
    """
    Records each drone handoff event during a mission.
    Used for analytics and mission activity tracking.
    """

    # Mission reference
    mission_id = StringField(required=True)
    mission_name = StringField()

    # Handoff details
    handoff_type = StringField(
        choices=[
            "start",                    # Mission started with initial drone
            "replacement_dispatched",   # Replacement drone sent to rendezvous
            "handoff_complete",         # Swap completed at 10m proximity
            "battery_handoff",          # DEPRECATED - kept for old data
            "return_to_base",           # Drone returned to base
            "mission_aborted",          # Mission aborted (no replacement available)
            "complete"                  # Mission completed
        ],
        required=True
    )

    # Outgoing drone (the one being replaced or returning)
    outgoing_drone_id = StringField()
    outgoing_drone_battery = FloatField()  # Battery level at handoff
    outgoing_drone_location = DictField()  # GeoJSON Point

    # Incoming drone (the replacement)
    incoming_drone_id = StringField()
    incoming_drone_battery = FloatField()  # Battery level at handoff

    # Base information
    base_id = StringField()
    base_name = StringField()

    # Mission state at handoff
    waypoint_index = IntField()
    mission_progress = FloatField()  # Percentage

    # Reason for handoff
    reason = StringField()  # e.g., "Low battery (18%)", "Mission start", etc.

    # Timestamps
    timestamp = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "drone_handoff_logs",
        "indexes": [
            "mission_id",
            "outgoing_drone_id",
            "incoming_drone_id",
            "timestamp",
            ("mission_id", "-timestamp"),  # For mission timeline queries
        ],
    }

    def __str__(self):
        return f"HandoffLog({self.mission_id}, {self.handoff_type})"


def log_handoff(
    mission,
    handoff_type: str,
    outgoing_drone=None,
    incoming_drone=None,
    base=None,
    waypoint_index: int = 0,
    reason: str = ""
) -> DroneHandoffLog:
    """
    Helper function to create a handoff log entry.
    
    Args:
        mission: Mission object
        handoff_type: Type of handoff event
        outgoing_drone: Drone being replaced (optional)
        incoming_drone: Replacement drone (optional)
        base: DroneBase object (optional)
        waypoint_index: Current waypoint index
        reason: Reason for handoff
        
    Returns:
        Created DroneHandoffLog entry
    """
    log = DroneHandoffLog(
        mission_id=mission.mission_id,
        mission_name=mission.name,
        handoff_type=handoff_type,
        waypoint_index=waypoint_index,
        mission_progress=mission.progress or 0,
        reason=reason,
    )

    if outgoing_drone:
        log.outgoing_drone_id = outgoing_drone.drone_id
        log.outgoing_drone_battery = outgoing_drone.battery_level
        if hasattr(outgoing_drone, 'location') and outgoing_drone.location:
            log.outgoing_drone_location = outgoing_drone.location

    if incoming_drone:
        log.incoming_drone_id = incoming_drone.drone_id
        log.incoming_drone_battery = incoming_drone.battery_level

    if base:
        log.base_id = base.base_id
        log.base_name = base.name

    log.save()
    return log


def get_mission_handoff_history(mission_id: str) -> list:
    """Get all handoff events for a mission, ordered by timestamp"""
    return list(
        DroneHandoffLog.objects(mission_id=mission_id).order_by("timestamp")
    )


def get_drone_activity(drone_id: str, limit: int = 50) -> list:
    """Get recent activity for a specific drone"""
    from mongoengine import Q
    return list(
        DroneHandoffLog.objects(
            Q(outgoing_drone_id=drone_id) | Q(incoming_drone_id=drone_id)
        ).order_by("-timestamp").limit(limit)
    )
