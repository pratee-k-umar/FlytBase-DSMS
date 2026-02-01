"""
Mission Index Endpoint
GET  /api/missions/     - List all missions
POST /api/missions/     - Create a new mission
"""
from dsms.api.bases import BaseEndpoint
from dsms.api.serializers.mission import MissionSerializer, MissionListSerializer, MissionCreateSerializer
from dsms.services import mission_service


class MissionIndexEndpoint(BaseEndpoint):
    """
    Endpoint for listing and creating missions.
    """
    
    def get(self, request):
        """List all missions with optional filters"""
        filters = {}
        
        # Parse query params
        if 'status' in request.query_params:
            filters['status'] = request.query_params['status']
        if 'site' in request.query_params:
            filters['site'] = request.query_params['site']
        if 'drone_id' in request.query_params:
            filters['drone_id'] = request.query_params['drone_id']
        
        missions = mission_service.list_missions(filters)
        
        # Apply pagination
        limit = request.query_params.get('limit')
        offset = request.query_params.get('offset', 0)
        
        if limit:
            limit = int(limit)
            offset = int(offset)
            missions = missions[offset:offset + limit]
        
        serializer = MissionListSerializer(missions, many=True)
        
        return self.respond({
            'data': serializer.data,
            'count': len(missions)
        })
    
    def post(self, request):
        """Create a new mission"""
        serializer = MissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        mission = mission_service.create_mission(serializer.validated_data)
        
        return self.respond_created({
            'data': MissionSerializer(mission).data
        })
