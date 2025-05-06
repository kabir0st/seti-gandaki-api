from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class AuthAPITests(APITestCase):

    def test_login(self):
        url = reverse('login')
        data = {'phone_number': 'testuser', 'password': 'testpassword'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_whoami(self):
        url = reverse('whoami')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer <token>'
                                )  # Replace <token> with a valid token
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_refresh(self):
        url = reverse('login_refresh')
        data = {
            'refresh': 'testrefreshtoken'
        }  # Replace with a valid refresh token
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout(self):
        url = reverse('logout')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer <token>'
                                )  # Replace <token> with a valid token
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_validate_code(self):
        url = reverse('validate_code')
        data = {'phone_number': 'testuser', 'code': '1234'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reset_password(self):
        url = reverse('reset_password')
        data = {
            'phone_number': 'testuser',
            'code': '1234',
            'password': 'newpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_forget_password(self):
        url = reverse('forget_password')
        data = {'phone_number': 'testuser'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
