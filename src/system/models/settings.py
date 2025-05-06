from core.utils.models.singleton import SingletonModel
from django.db import models


class GlobalSettings(SingletonModel):
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    mobile = models.CharField(max_length=255, null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    business_name = models.CharField(max_length=255, default='Seti Gandaki')
    pan_number = models.CharField(max_length=255, default='')
