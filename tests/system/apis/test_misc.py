from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User


class MiscAPITests(APITestCase):

    def setUp(self):
        self.staff_user = User.objects.create_user(username='staff',
                                                   password='password',
                                                   is_staff=True)
        self.client.force_authenticate(user=self.staff_user)

    def test_document_list(self):
        url = reverse('documentapi-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_faq_list(self):
        url = reverse('faqapi-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_global_settings_list(self):
        url = reverse('globalsettingsapi-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_inquiries_list(self):
        url = reverse('inquiriesapi-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
