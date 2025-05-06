"""
Notification model for storing user notifications.
"""
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.utils.models import DefaultModel

from .user import UserBase


class Notification(DefaultModel):
    """
    Model for storing user notifications.
    """
    user = models.ForeignKey(UserBase, on_delete=models.CASCADE)
    msg = models.TextField(default='')
    redirect_url = models.TextField(default='')
    model = models.CharField(max_length=255)
    priority = models.IntegerField(default=5)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.msg}'

    def save(self, *args, **kwargs):
        """
        Override save method to clean up old read notifications.
        """
        super(Notification, self).save(*args, **kwargs)
        self._cleanup_old_notifications()

    def _cleanup_old_notifications(self):
        """
        Delete old read notifications, keeping only the 50 most recent.
        """
        if self.read:
            notifications = Notification.objects.filter(
                user=self.user, read=True).order_by('-id')
            if notifications.count() > 50:
                notifications[50:].delete()


@receiver(post_save, sender=Notification)
def delete_read_notifications(sender, instance, **kwargs):
    """
    Signal handler to clean up old read notifications.
    """
    if instance.read:
        instance._cleanup_old_notifications()


@receiver(post_save, sender=Notification)
def send_live_notification(sender, instance, created, **kwargs):
    """
    Signal handler to send real-time notifications via WebSocket.
    """
    if created:
        from system.services.notification_service import NotificationService

        # Send the notification to the user's group
        NotificationService.send_websocket_notification(
            user_id=instance.user.id,
            data={
                "id": str(instance.id),
                "msg": instance.msg,
                "redirect_url": instance.redirect_url,
                "model": instance.model,
                "priority": instance.priority,
                "read": instance.read,
                "created_at": instance.created_at.isoformat(),
            })
