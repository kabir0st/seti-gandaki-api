from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from system.models import Notification


class NotificationsAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser',
                                             password='password')
        self.client.force_authenticate(user=self.user)

    def test_notification_list(self):
        url = reverse('notification-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_notification_unread(self):
        url = reverse('notification-unread')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_notification_count(self):
        url = reverse('notification-count')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_notification_mark_as_read(self):
        url = reverse('notification-mark_as_read')
        # Create a notification for the user
        notification = Notification.objects.create(user=self.user,
                                                   message='Test notification')
        data = {'notification_ids': [notification.id]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_notification_mark_all_as_read(self):
        url = reverse('notification-mark_all_as_read')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
