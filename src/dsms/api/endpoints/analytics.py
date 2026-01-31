"""
Analytics Endpoints
GET /api/analytics/summary/  - Get organization-wide analytics
"""
from dsms.api.bases import BaseEndpoint
from dsms.services import analytics_service


class AnalyticsSummaryEndpoint(BaseEndpoint):
    """
    Endpoint for organization-wide analytics and statistics.
    """
    
    def get(self, request):
        """Get analytics summary"""
        summary = analytics_service.get_summary()
        return self.respond({'data': summary})
