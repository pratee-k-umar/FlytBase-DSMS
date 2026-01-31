"""
Drone Index Endpoint
GET  /api/fleet/drones/  - List all drones
POST /api/fleet/drones/  - Register a new drone
"""
from dsms.api.bases import BaseEndpoint
from dsms.api.serializers.drone import DroneSerializer, DroneCreateSerializer
from dsms.services import fleet_service


class DroneIndexEndpoint(BaseEndpoint):
    """
    Endpoint for listing and registering drones.
    """
    
    def get(self, request):
        """List all drones with optional filters"""
        filters = {}
        
        if 'status' in request.query_params:
            filters['status'] = request.query_params['status']
        if 'site' in request.query_params:
            filters['site'] = request.query_params['site']
        
        drones = fleet_service.list_drones(filters)
        serializer = DroneSerializer(drones, many=True)
        
        return self.respond({
            'data': serializer.data,
            'count': len(drones)
        })
    
    def post(self, request):
        """Register a new drone"""
        serializer = DroneCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        drone = fleet_service.create_drone(serializer.validated_data)
        
        return self.respond_created({
            'data': DroneSerializer(drone).data
        })
