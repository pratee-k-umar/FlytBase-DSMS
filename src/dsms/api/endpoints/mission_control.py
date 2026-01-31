"""
Mission Control Endpoints
POST /api/missions/<id>/start/         - Start mission
POST /api/missions/<id>/pause/         - Pause mission
POST /api/missions/<id>/resume/        - Resume mission
POST /api/missions/<id>/abort/         - Abort mission
POST /api/missions/<id>/generate-path/ - Generate flight path
"""
from dsms.api.bases import BaseEndpoint
from dsms.api.serializers.mission import MissionSerializer
from dsms.services import mission_service


class MissionStartEndpoint(BaseEndpoint):
    """Start a mission"""
    
    def post(self, request, mission_id):
        mission = mission_service.start_mission(mission_id)
        return self.respond({
            'message': 'Mission started',
            'mission': MissionSerializer(mission).data
        })


class MissionPauseEndpoint(BaseEndpoint):
    """Pause a running mission"""
    
    def post(self, request, mission_id):
        mission = mission_service.pause_mission(mission_id)
        return self.respond({
            'message': 'Mission paused',
            'mission': MissionSerializer(mission).data
        })


class MissionResumeEndpoint(BaseEndpoint):
    """Resume a paused mission"""
    
    def post(self, request, mission_id):
        mission = mission_service.resume_mission(mission_id)
        return self.respond({
            'message': 'Mission resumed',
            'mission': MissionSerializer(mission).data
        })


class MissionAbortEndpoint(BaseEndpoint):
    """Abort a mission"""
    
    def post(self, request, mission_id):
        mission = mission_service.abort_mission(mission_id)
        return self.respond({
            'message': 'Mission aborted',
            'mission': MissionSerializer(mission).data
        })


class MissionGeneratePathEndpoint(BaseEndpoint):
    """Generate flight path for a mission"""
    
    def post(self, request, mission_id):
        mission = mission_service.generate_flight_path(mission_id)
        return self.respond({
            'message': 'Flight path generated',
            'mission': MissionSerializer(mission).data
        })
