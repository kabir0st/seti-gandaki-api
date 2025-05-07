from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from system.models.user import UserBase


class TestAuthAPI(APITestCase):

    def test_register_user(self):
        url = reverse("RegisterUsers")
        data = {
            "email": "test@example.com",
            "password": "testpassword",
            "phone_number": "1234567890"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            UserBase.objects.filter(email="test@example.com").exists())

    def test_login_user(self):
        url = reverse("AuthLogin")
        UserBase.objects.create_user(email="test@example.com",
                                     password="testpassword",
                                     phone_number="1234567890",
                                     is_staff=True)
        data = {
            "email": "test@example.com",
            "password": "testpassword",
            "phone_number": "1234567890"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])

    def test_logout_user(self):
        url = reverse("AuthLogout")
        user = UserBase.objects.create_user(email="test@example.com",
                                            password="testpassword",
                                            phone_number="1234567890",
                                            is_staff=True)
        self.client.force_authenticate(user=user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
