from django.apps import AppConfig


class StatementsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'statements'

    def ready(self):
        import statements.signals
