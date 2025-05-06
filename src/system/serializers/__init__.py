# Import all serializers to make them available through the package
# This allows imports like:
# from system.serializers import NotificationSerializer
from system.serializers.notifications import (NotificationSerializer,
                                              NotificationReadSerializer)

# Silence flake8 unused import warnings
__all__ = ['NotificationSerializer', 'NotificationReadSerializer']
