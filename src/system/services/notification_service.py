"""
Notification service for sending notifications to users.
This service follows DRY principles by centralizing notification logic.
"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Q

from system.models import Notification, UserBase


class NotificationService:
    """
    Service class for handling notifications.
    This centralizes all notification-related functionality.
    """

    @staticmethod
    def create_notification(user,
                            message,
                            redirect_url="",
                            model="",
                            priority=5):
        """
        Create a notification for a user.
        
        Args:
            user: The user to notify (UserBase instance or user ID)
            message: The notification message
            redirect_url: URL to redirect to when clicking the notification
            model: Related model name
            priority: Notification priority (1-5, with 1 being highest)
            
        Returns:
            The created Notification instance
        """
        if isinstance(user, int):
            user = UserBase.objects.get(id=user)

        notification = Notification.objects.create(user=user,
                                                   msg=message,
                                                   redirect_url=redirect_url,
                                                   model=model,
                                                   priority=priority)

        return notification

    @staticmethod
    def create_bulk_notifications(users,
                                  message,
                                  redirect_url="",
                                  model="",
                                  priority=5):
        """
        Create notifications for multiple users.
        
        Args:
            users: QuerySet or list of UserBase instances
            message: The notification message
            redirect_url: URL to redirect to when clicking the notification
            model: Related model name
            priority: Notification priority (1-5, with 1 being highest)
            
        Returns:
            List of created Notification instances
        """
        notifications = []

        for user in users:
            notification = NotificationService.create_notification(
                user=user,
                message=message,
                redirect_url=redirect_url,
                model=model,
                priority=priority)
            notifications.append(notification)

        return notifications

    @staticmethod
    def create_staff_notification(message,
                                  redirect_url="",
                                  model="",
                                  priority=5):
        """
        Create notifications for all staff users.
        
        Args:
            message: The notification message
            redirect_url: URL to redirect to when clicking the notification
            model: Related model name
            priority: Notification priority (1-5, with 1 being highest)
            
        Returns:
            List of created Notification instances
        """
        staff_users = UserBase.objects.filter(
            Q(is_staff=True) | Q(is_superuser=True))
        return NotificationService.create_bulk_notifications(
            users=staff_users,
            message=message,
            redirect_url=redirect_url,
            model=model,
            priority=priority)

    @staticmethod
    def mark_as_read(notification_ids, user):
        """
        Mark notifications as read.
        
        Args:
            notification_ids: List of notification IDs
            user: The user who owns the notifications
            
        Returns:
            Number of notifications marked as read
        """
        return Notification.objects.filter(id__in=notification_ids,
                                           user=user).update(read=True)

    @staticmethod
    def get_unread_count(user):
        """
        Get the count of unread notifications for a user.
        
        Args:
            user: The user to check
            
        Returns:
            Count of unread notifications
        """
        return Notification.objects.filter(user=user, read=False).count()

    @staticmethod
    def get_notifications(user, limit=20, include_read=False):
        """
        Get notifications for a user.
        
        Args:
            user: The user to get notifications for
            limit: Maximum number of notifications to return
            include_read: Whether to include read notifications
            
        Returns:
            QuerySet of Notification instances
        """
        query = Notification.objects.filter(user=user)

        if not include_read:
            query = query.filter(read=False)

        return query.order_by('-created_at')[:limit]

    @staticmethod
    def send_websocket_notification(user_id, data):
        """
        Send a notification via WebSocket.
        
        Args:
            user_id: The ID of the user to send the notification to
            data: The notification data to send
            
        Returns:
            None
        """
        channel_layer = get_channel_layer()
        group_name = f"user_{user_id}"

        async_to_sync(channel_layer.group_send)(group_name, {
            "type": "notification.message",
            "notification": data
        })
