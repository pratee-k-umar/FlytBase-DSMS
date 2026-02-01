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
        # Get all completed missions for aggregate stats
        completed_missions = list(Mission.objects(status="completed"))
        
        # Calculate aggregate metrics
        total_area_covered = sum(m.area_covered or 0 for m in completed_missions)
        total_images = sum(m.images_captured or 0 for m in completed_missions)
        total_flight_time = 0
        for m in completed_missions:
            if m.started_at and m.completed_at:
                duration = (m.completed_at - m.started_at).total_seconds() / 60  # minutes
                total_flight_time += duration
        
        stats = {
            "total": Mission.objects.count(),
            "draft": Mission.objects(status="draft").count(),
            "scheduled": Mission.objects(status="scheduled").count(),
            "in_progress": Mission.objects(status="in_progress").count(),
            "paused": Mission.objects(status="paused").count(),
            "completed": Mission.objects(status="completed").count(),
            "aborted": Mission.objects(status="aborted").count(),
            "failed": Mission.objects(status="failed").count(),
            # Aggregate metrics
            "total_area_covered": total_area_covered,
            "total_images_captured": total_images,
            "total_flight_time": total_flight_time,  # in minutes
            "avg_flight_time": total_flight_time / len(completed_missions) if completed_missions else 0,
        }

        return self.respond(stats)
