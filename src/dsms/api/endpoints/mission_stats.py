"""
Mission Stats Endpoint
GET /api/missions/stats/ - Get mission statistics
"""

from dsms.api.bases import BaseEndpoint
from dsms.models.mission import Mission


class MissionStatsEndpoint(BaseEndpoint):
    """
    Endpoint for mission statistics.
    """

    def get(self, request):
        """Get mission statistics"""
        stats = {
            "total": Mission.objects.count(),
            "draft": Mission.objects(status="draft").count(),
            "scheduled": Mission.objects(status="scheduled").count(),
            "in_progress": Mission.objects(status="in_progress").count(),
            "paused": Mission.objects(status="paused").count(),
            "completed": Mission.objects(status="completed").count(),
            "aborted": Mission.objects(status="aborted").count(),
            "failed": Mission.objects(status="failed").count(),
        }

        return self.respond(stats)
