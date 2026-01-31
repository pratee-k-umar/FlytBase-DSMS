"""
Telemetry Service
Business logic for handling real-time telemetry data.
"""

from datetime import datetime
from typing import Any, Dict, List

from dsms.db import connect_db

# Ensure DB connection
connect_db()

from dsms.models import TelemetryPoint


def record_telemetry(data: Dict[str, Any]) -> TelemetryPoint:
    """Record a telemetry data point"""
    # Extract position - handle both GeoJSON and direct lat/lng/alt
    if "location" in data:
        location = data["location"]
        if isinstance(location, dict) and "coordinates" in location:
            # GeoJSON format: {type: 'Point', coordinates: [lng, lat]}
            coords = location["coordinates"]
            position = {
                "lat": coords[1],
                "lng": coords[0],
                "alt": data.get("altitude", 0),
            }
        else:
            position = location
    elif "position" in data:
        position = data["position"]
    else:
        position = {"lat": 0, "lng": 0, "alt": 0}

    point = TelemetryPoint(
        mission_id=data["mission_id"],
        drone_id=data["drone_id"],
        timestamp=data.get("timestamp", datetime.utcnow()),
        position=position,
        battery=data.get("battery_level", data.get("battery", 100)),
        altitude_agl=data.get("altitude", 0),
        heading=data.get("heading", 0),
        speed=data.get("speed", 0),
        waypoint_index=data.get(
            "current_waypoint_index", data.get("waypoint_index", 0)
        ),
        progress=data.get("progress", 0),
        status=data.get("status", "flying"),
    )
    point.save()
    return point


def get_mission_telemetry(
    mission_id: str, limit: int = 100, since: datetime = None
) -> List[TelemetryPoint]:
    """Get telemetry points for a mission"""
    queryset = TelemetryPoint.objects.filter(mission_id=mission_id)

    if since:
        queryset = queryset.filter(timestamp__gt=since)

    return list(queryset.order_by("-timestamp").limit(limit))


def get_latest_telemetry(mission_id: str) -> TelemetryPoint:
    """Get the most recent telemetry point for a mission"""
    points = (
        TelemetryPoint.objects.filter(mission_id=mission_id)
        .order_by("-timestamp")
        .limit(1)
    )

    return points[0] if points else None
