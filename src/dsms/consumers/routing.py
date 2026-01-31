"""
WebSocket URL Routing
"""
from django.urls import re_path
from dsms.consumers.telemetry import TelemetryConsumer

websocket_urlpatterns = [
    re_path(
        r'ws/missions/(?P<mission_id>\w+)/telemetry/$',
        TelemetryConsumer.as_asgi()
    ),
]
