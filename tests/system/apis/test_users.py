from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from system.models import UserBase


class UsersAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser',
                                             password='password')
        self.client.force_authenticate(user=self.user)
        self.staff_user = User.objects.create_user(username='staff',
                                                   password='password',
                                                   is_staff=True)

    def test_register_user(self):
        url = reverse('registeruserbaseapi-list')
        data = {'phone_number': 'newuser', 'password': 'newpassword'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_list(self):
        self.client.force_authenticate(user=self.staff_user)
        url = reverse('userbaseapi-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_retrieve(self):
        self.client.force_authenticate(user=self.staff_user)
        user = UserBase.objects.create(phone_number='test', password='test')
        url = reverse('userbaseapi-detail', kwargs={'uuid': user.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_update_password(self):
        url = reverse('userbaseapi-update_password',
                      kwargs={'uuid': self.user.uuid})
        data = {'password': 'newpassword'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_verify(self):
        self.client.force_authenticate(user=self.staff_user)
        user = UserBase.objects.create(phone_number='test1', password='test1')
        url = reverse('userbaseapi-verify', kwargs={'uuid': user.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_toggle_activation(self):
        self.client.force_authenticate(user=self.staff_user)
        user = UserBase.objects.create(phone_number='test2', password='test2')
        url = reverse('userbaseapi-toggle-activation',
                      kwargs={'uuid': user.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
