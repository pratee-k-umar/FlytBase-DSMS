"""
Mission Details Endpoint
GET    /api/missions/<id>/  - Get mission details
PATCH  /api/missions/<id>/  - Update mission
DELETE /api/missions/<id>/  - Delete mission
"""
from dsms.api.bases import BaseEndpoint
from dsms.api.serializers.mission import MissionSerializer, MissionUpdateSerializer
from dsms.services import mission_service


class MissionDetailsEndpoint(BaseEndpoint):
    """
    Endpoint for single mission operations.
    """
    
    def get(self, request, mission_id):
        """Get mission details"""
        mission = mission_service.get_mission(mission_id)
        serializer = MissionSerializer(mission)
        return self.respond({'data': serializer.data})
    
    def patch(self, request, mission_id):
        """Update mission"""
        serializer = MissionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        mission = mission_service.update_mission(mission_id, serializer.validated_data)
        return self.respond({'data': MissionSerializer(mission).data})
    
    def delete(self, request, mission_id):
        """Delete mission"""
        mission_service.delete_mission(mission_id)
        return self.respond_no_content()
