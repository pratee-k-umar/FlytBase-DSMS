"""
DSMS URL Configuration
"""

import os

from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.urls import include, path, re_path
from django.views.static import serve
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health_check(request):
    """Health check endpoint"""
    return Response({"status": "ok", "service": "dsms-api"})


def serve_frontend(request):
    """Serve the React frontend index.html"""
    # Look for index.html in dist folder (Webpack build output)
    dist_path = os.path.join(settings.BASE_DIR.parent.parent, 'dist', 'index.html')
    
    if os.path.exists(dist_path):
        with open(dist_path, 'r') as f:
            return HttpResponse(f.read(), content_type='text/html')
    else:
        # Fallback: return API info if frontend not built
        return HttpResponse("""
        <html>
        <head><title>DSMS API</title></head>
        <body>
            <h1>DSMS - Drone Survey Management System</h1>
            <p>API Endpoints:</p>
            <ul>
                <li><a href="/health/">/health/</a> - Health check</li>
                <li><a href="/api/missions/">/api/missions/</a> - Missions</li>
                <li><a href="/api/fleet/drones/">/api/fleet/drones/</a> - Drones</li>
                <li><a href="/api/fleet/stats/">/api/fleet/stats/</a> - Fleet stats</li>
            </ul>
        </body>
        </html>
        """, content_type='text/html')


urlpatterns = [
    path("api/", include("dsms.api.urls")),
    path("health/", health_check, name="health-check"),
    path("", serve_frontend, name="frontend"),
]

# Serve static files from dist folder (Webpack build output)
DIST_DIR = os.path.join(settings.BASE_DIR.parent.parent, 'dist')
if os.path.exists(DIST_DIR):
    urlpatterns += [
        re_path(r'^(?P<path>.*\.(js|css|png|jpg|svg|ico|map))$', 
                serve, {'document_root': DIST_DIR}),
    ]

# Serve static files in production
if not settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
