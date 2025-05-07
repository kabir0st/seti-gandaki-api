from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from system.models.user import UserBase


class TestRegistrationAPI(APITestCase):

    def test_successful_registration(self):
        url = reverse("RegisterUsers")
        data = {
            "email": "newuser@example.com",
            "password": "securepassword123",
            "phone_number": "0987654321"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            UserBase.objects.filter(email="newuser@example.com").exists())
        user = UserBase.objects.get(email="newuser@example.com")
        self.assertTrue(user.check_password("securepassword123"))

    def test_registration_missing_fields(self):
        url = reverse("RegisterUsers")
        data = {
            "email": "incomplete@example.com",
            # password and phone_number are missing
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertIn("phone_number", response.data)

    def test_registration_invalid_email(self):
        url = reverse("RegisterUsers")
        data = {
            "email": "invalid-email",
            "password": "password123",
            "phone_number": "1122334455"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    # Assuming there are password validation requirements
    # def test_registration_weak_password(self):
    #     url = reverse("RegisterUsers")
    #     data = {
    #         "email": "weakpass@example.com",
    #         "password": "short", # Assuming 'short' is a weak password
    #         "phone_number": "5544332211"
    #     }
    #     response = self.client.post(url, data)
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertIn("password", response.data)

    def test_registration_duplicate_email(self):
        url = reverse("RegisterUsers")
        # Register a user first
        UserBase.objects.create_user(email="existing@example.com",
                                     password="password123",
                                     phone_number="1112223334",
                                     is_staff=True)

        # Attempt to register with the same email
        data = {
            "email": "existing@example.com",
            "password": "anotherpassword",
            "phone_number": "9988776655"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
