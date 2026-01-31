"""
API URL routing.
Sentry pattern: All API routes defined in one place.
"""

from django.urls import path

from dsms.api.endpoints import (
    analytics,
    drone_details,
    drone_index,
    fleet_stats,
    mission_control,
    mission_details,
    mission_index,
    mission_stats,
    simulator,
    telemetry,
)

urlpatterns = [
    # Missions
    path(
        "missions/", mission_index.MissionIndexEndpoint.as_view(), name="mission-list"
    ),
    path(
        "missions/stats/",
        mission_stats.MissionStatsEndpoint.as_view(),
        name="mission-stats",
    ),
    path(
        "missions/<str:mission_id>/",
        mission_details.MissionDetailsEndpoint.as_view(),
        name="mission-detail",
    ),
    path(
        "missions/<str:mission_id>/start/",
        mission_control.MissionStartEndpoint.as_view(),
        name="mission-start",
    ),
    path(
        "missions/<str:mission_id>/pause/",
        mission_control.MissionPauseEndpoint.as_view(),
        name="mission-pause",
    ),
    path(
        "missions/<str:mission_id>/resume/",
        mission_control.MissionResumeEndpoint.as_view(),
        name="mission-resume",
    ),
    path(
        "missions/<str:mission_id>/abort/",
        mission_control.MissionAbortEndpoint.as_view(),
        name="mission-abort",
    ),
    path(
        "missions/<str:mission_id>/generate-path/",
        mission_control.MissionGeneratePathEndpoint.as_view(),
        name="mission-generate-path",
    ),
    path(
        "missions/<str:mission_id>/simulate/",
        simulator.SimulatorStartEndpoint.as_view(),
        name="mission-simulate",
    ),
    path(
        "missions/<str:mission_id>/telemetry/",
        telemetry.MissionTelemetryEndpoint.as_view(),
        name="mission-telemetry",
    ),
    # Fleet / Drones
    path("fleet/drones/", drone_index.DroneIndexEndpoint.as_view(), name="drone-list"),
    path(
        "fleet/drones/<str:drone_id>/",
        drone_details.DroneDetailsEndpoint.as_view(),
        name="drone-detail",
    ),
    path("fleet/stats/", fleet_stats.FleetStatsEndpoint.as_view(), name="fleet-stats"),
    # Analytics
    path(
        "analytics/summary/",
        analytics.AnalyticsSummaryEndpoint.as_view(),
        name="analytics-summary",
    ),
]
