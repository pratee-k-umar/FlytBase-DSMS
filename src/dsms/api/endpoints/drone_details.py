"""
Drone Details Endpoint
GET   /api/fleet/drones/<id>/  - Get drone details
PATCH /api/fleet/drones/<id>/  - Update drone
"""
from dsms.api.bases import BaseEndpoint
from dsms.api.serializers.drone import DroneSerializer, DroneUpdateSerializer
from dsms.services import fleet_service


class DroneDetailsEndpoint(BaseEndpoint):
    """
    Endpoint for single drone operations.
    """
    
    def get(self, request, drone_id):
        """Get drone details"""
        drone = fleet_service.get_drone(drone_id)
        serializer = DroneSerializer(drone)
        return self.respond({'data': serializer.data})
    
    def patch(self, request, drone_id):
        """Update drone"""
        serializer = DroneUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        drone = fleet_service.update_drone(drone_id, serializer.validated_data)
        return self.respond({'data': DroneSerializer(drone).data})
