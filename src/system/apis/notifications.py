"""
API views for notifications.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.utils.viewsets import ModelViewSet
from system.models import Notification
from system.serializers.notifications import (NotificationSerializer,
                                              NotificationReadSerializer)
from system.services.notification_service import NotificationService


class NotificationViewSet(ModelViewSet):
    """
    ViewSet for managing notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return notifications for the current user.
        """
        return Notification.objects.filter(
            user=self.request.user).order_by('-created_at')

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """
        Get unread notifications for the current user.
        """
        unread_notifications = Notification.objects.filter(
            user=request.user, read=False).order_by('-created_at')

        page = self.paginate_queryset(unread_notifications)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(unread_notifications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def count(self, request):
        """
        Get the count of unread notifications for the current user.
        """
        count = NotificationService.get_unread_count(request.user)
        return Response({'count': count})

    @action(detail=False, methods=['post'])
    def mark_as_read(self, request):
        """
        Mark notifications as read.
        """
        serializer = NotificationReadSerializer(data=request.data)
        if serializer.is_valid():
            notification_ids = serializer.validated_data['notification_ids']
            updated_count = NotificationService.mark_as_read(
                notification_ids=notification_ids, user=request.user)
            return Response({
                'success': True,
                'message': f'Marked {updated_count} notifications as read',
                'updated_count': updated_count
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """
        Mark all notifications as read.
        """
        notification_ids = list(
            Notification.objects.filter(user=request.user,
                                        read=False).values_list('id',
                                                                flat=True))

        updated_count = NotificationService.mark_as_read(
            notification_ids=notification_ids, user=request.user)

        return Response({
            'success': True,
            'message': f'Marked {updated_count} notifications as read',
            'updated_count': updated_count
        })
