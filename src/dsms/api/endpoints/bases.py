"""
Base Endpoints
API endpoints for drone base management.
"""

from dsms.api.bases import BaseEndpoint
from dsms.api.serializers.base import (
    AddDroneToBaseSerializer,
    BaseStatsSerializer,
    CreateBaseSerializer,
    DroneBaseSerializer,
    NearestBaseQuerySerializer,
    UpdateBaseSerializer,
)
from dsms.api.serializers.drone import DroneSerializer
from dsms.services import base_service


class BaseListEndpoint(BaseEndpoint):
    """
    GET /api/bases/ - List all bases
    POST /api/bases/ - Create a new base
    """

    def get(self, request):
        """List all bases with optional filters"""
        filters = {}
        if "status" in request.query_params:
            filters["status"] = request.query_params["status"]
        if "region" in request.query_params:
            filters["region"] = request.query_params["region"]

        bases = base_service.list_bases(filters)
        serializer = DroneBaseSerializer(bases, many=True)

        return self.respond(
            {
                "data": serializer.data,
                "count": len(bases),
            }
        )

    def post(self, request):
        """Create a new drone base"""
        serializer = CreateBaseSerializer(data=request.data)
        if not serializer.is_valid():
            return self.respond_error(serializer.errors, status_code=400)

        base = base_service.create_base(serializer.validated_data)
        return self.respond_created(DroneBaseSerializer(base).data)


class BaseDetailEndpoint(BaseEndpoint):
    """
    GET /api/bases/{id}/ - Get base details
    PUT /api/bases/{id}/ - Update base
    DELETE /api/bases/{id}/ - Delete base
    """

    def get(self, request, base_id):
        """Get base details"""
        base = base_service.get_base(base_id)
        return self.respond(DroneBaseSerializer(base).data)

    def put(self, request, base_id):
        """Update base"""
        serializer = UpdateBaseSerializer(data=request.data)
        if not serializer.is_valid():
            return self.respond_error(serializer.errors, status=400)

        base = base_service.update_base(base_id, serializer.validated_data)
        return self.respond(DroneBaseSerializer(base).data)

    def delete(self, request, base_id):
        """Delete base"""
        base_service.delete_base(base_id)
        return self.respond({"message": "Base deleted successfully"})


class BaseDronesEndpoint(BaseEndpoint):
    """
    GET /api/bases/{id}/drones/ - List drones at base
    POST /api/bases/{id}/drones/ - Add drone to base
    """

    def get(self, request, base_id):
        """List drones at this base"""
        drones = base_service.get_drones_at_base(base_id)
        serializer = DroneSerializer(drones, many=True)

        return self.respond(
            {
                "data": serializer.data,
                "count": len(drones),
            }
        )

    def post(self, request, base_id):
        """Add a drone to this base"""
        serializer = AddDroneToBaseSerializer(data=request.data)
        if not serializer.is_valid():
            return self.respond_error(serializer.errors, status=400)

        drone = base_service.add_drone_to_base(
            base_id,
            serializer.validated_data["drone_id"],
        )
        return self.respond(DroneSerializer(drone).data)


class BaseStatsEndpoint(BaseEndpoint):
    """
    GET /api/bases/stats/ - Get base statistics
    """

    def get(self, request):
        """Get overall base statistics"""
        stats = base_service.get_base_stats()
        return self.respond(stats)


class NearestBaseEndpoint(BaseEndpoint):
    """
    GET /api/bases/nearest/?lat=X&lng=Y - Find nearest base
    """

    def get(self, request):
        """Find nearest base to a location"""
        serializer = NearestBaseQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return self.respond_error(serializer.errors, status=400)

        lat = serializer.validated_data["lat"]
        lng = serializer.validated_data["lng"]

        base = base_service.find_nearest_base(lat, lng)
        if not base:
            return self.respond_error("No active bases found", status=404)

        return self.respond(DroneBaseSerializer(base).data)
