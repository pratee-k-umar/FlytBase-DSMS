"""
Fleet Stats Endpoint
GET /api/fleet/stats/  - Get fleet statistics
"""
from dsms.api.bases import BaseEndpoint
from dsms.services import fleet_service


class FleetStatsEndpoint(BaseEndpoint):
    """
    Endpoint for fleet-wide statistics.
    """
    
    def get(self, request):
        """Get fleet statistics"""
        stats = fleet_service.get_fleet_stats()
        return self.respond({'data': stats})
