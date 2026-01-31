"""
Django App Configuration with startup hooks
"""

from django.apps import AppConfig


class DsmsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dsms"

    def ready(self):
        """
        Called when Django is ready.
        Use this to restart any in-progress mission simulations.
        """
        # Import here to avoid circular imports
        import threading

        from dsms.db import connect_db

        # Ensure DB connection
        connect_db()

        from dsms.models import Mission
        from dsms.tasks.simulator import run_mission_simulation_sync

        # Find all missions that are in progress
        try:
            in_progress_missions = Mission.objects.filter(status="in_progress")

            for mission in in_progress_missions:
                print(
                    f"[STARTUP] Restarting simulator for mission {mission.mission_id}"
                )

                # Restart simulator thread
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
