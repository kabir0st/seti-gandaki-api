from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class LogsAPITests(APITestCase):

    def test_auth_log_list(self):
        url = reverse('authlogapi-list')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer <token>'
                                )  # Replace <token> with a valid token
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_audit_log_list(self):
        url = reverse('auditlogapi-list')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer <token>'
                                )  # Replace <token> with a valid token
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
