"""
Telemetry API Endpoint
"""

from rest_framework import status
from rest_framework.response import Response

from dsms.api.bases import BaseEndpoint
from dsms.services import telemetry_service
from dsms.utils.exceptions import NotFoundError


class MissionTelemetryEndpoint(BaseEndpoint):
    """
    GET /api/missions/<mission_id>/telemetry/
    Get telemetry data for a mission.
    Query params:
    - limit: number of telemetry points to return (default: 100)
    """

    def get(self, request, mission_id: str):
        try:
            limit = int(request.GET.get("limit", 100))
            telemetry = telemetry_service.get_mission_telemetry(
                mission_id=mission_id, limit=limit
            )

            # Serialize telemetry data
            data = []
            for point in telemetry:
                data.append(
                    {
                        "mission_id": point.mission_id,
                        "drone_id": point.drone_id,
                        "timestamp": point.timestamp.isoformat(),
                        "position": point.position,
                        "battery": point.battery,
                        "speed": point.speed,
                        "heading": point.heading,
                        "altitude_agl": point.altitude_agl,
                        "waypoint_index": point.waypoint_index,
                        "progress": point.progress,
                        "status": point.status,
                    }
                )

            return Response({"data": data}, status=status.HTTP_200_OK)

        except NotFoundError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {"error": f"Failed to fetch telemetry: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
