"""
Mission Details Endpoint
GET    /api/missions/<id>/  - Get mission details
PATCH  /api/missions/<id>/  - Update mission
DELETE /api/missions/<id>/  - Delete mission
GET    /api/missions/<id>/handoffs/ - Get mission handoff history
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


class MissionHandoffHistoryEndpoint(BaseEndpoint):
    """
    Endpoint for getting mission handoff history.
    Shows all drones used during a mission, when they were replaced, and why.
    """
    
    def get(self, request, mission_id):
        """Get all handoff events for a mission"""
        from dsms.models import get_mission_handoff_history
        
        handoffs = get_mission_handoff_history(mission_id)
        
        # Serialize handoff data
        data = []
        for h in handoffs:
            data.append({
                "handoff_type": h.handoff_type,
                "timestamp": h.timestamp.isoformat() if h.timestamp else None,
                "outgoing_drone": {
                    "drone_id": h.outgoing_drone_id,
                    "battery_level": h.outgoing_drone_battery,
                } if h.outgoing_drone_id else None,
                "incoming_drone": {
                    "drone_id": h.incoming_drone_id,
                    "battery_level": h.incoming_drone_battery,
                } if h.incoming_drone_id else None,
                "base": {
                    "base_id": h.base_id,
                    "name": h.base_name,
                } if h.base_id else None,
                "waypoint_index": h.waypoint_index,
                "mission_progress": h.mission_progress,
                "reason": h.reason,
            })
        
        return self.respond({
            'mission_id': mission_id,
            'handoff_count': len(data),
            'drones_used': len(set(
                [h['incoming_drone']['drone_id'] for h in data if h.get('incoming_drone')]
            )),
            'handoffs': data
        })
