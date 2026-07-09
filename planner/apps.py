from django.apps import AppConfig

class PlannerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'planner'

    def ready(self):
        pass  # Previously had MongoDB import here, safely removed
