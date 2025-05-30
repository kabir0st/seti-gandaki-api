from core.utils.models.singleton import SingletonModel
from django.db import models


class GlobalSettings(SingletonModel):
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    mobile = models.CharField(max_length=255, null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    business_name = models.CharField(max_length=255, default='Seti Gandaki')
    pan_number = models.CharField(max_length=255, default='')
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    multi_vendor_support = models.BooleanField(default=False)
