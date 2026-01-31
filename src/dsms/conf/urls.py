"""
DSMS URL Configuration
"""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health_check(request):
    """Health check endpoint"""
    return Response({"status": "ok", "service": "dsms-api"})


# Auto-restart simulators for in-progress missions on startup
def restart_simulators():
    """Restart simulator threads for missions that were in progress"""
    import threading

    from dsms.db import connect_db

    try:
        connect_db()
        from dsms.models import Mission
        from dsms.services import fleet_service
        from dsms.tasks.simulator import run_mission_simulation_sync

        # Fix stale drone statuses first
        fixed_count = fleet_service.fix_stale_drone_statuses()
        if fixed_count > 0:
            print(f"[STARTUP] Fixed {fixed_count} drones with stale statuses")

        # Restart simulators for in-progress missions
        in_progress_missions = Mission.objects.filter(status="in_progress")

        for mission in in_progress_missions:
            print(f"[STARTUP] Restarting simulator for mission {mission.mission_id}")

            thread = threading.Thread(
                target=run_mission_simulation_sync,
                args=(mission.mission_id,),
                daemon=True,
            )
            thread.start()
            print(
                f"[STARTUP] Simulator thread restarted for mission {mission.mission_id}"
            )

    except Exception as e:
        print(f"[STARTUP ERROR] Could not restart simulators: {e}")


# Run once on module load
restart_simulators()


urlpatterns = [
    path("api/", include("dsms.api.urls")),
    path("health/", health_check, name="health-check"),
]

# Serve static files in production
if not settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# In development, Webpack dev server handles frontend
# In production, serve React app from dist/ folder (add later when deploying)
