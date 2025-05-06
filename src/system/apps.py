from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save


class SystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'system'

    def ready(self):
        from django.apps import apps

        from core.global_signals import invalidate_model_cache

        for model in apps.get_models():
            post_save.connect(invalidate_model_cache, sender=model)
            post_delete.connect(invalidate_model_cache, sender=model)
