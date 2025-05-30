from decimal import Decimal
from django.core.validators import validate_image_file_extension
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.utils.functions import limit_size  # Removed default_json

# Removed UserBase import as it's no longer used in this file


class Staff(models.Model):
    name = models.CharField(_("Full Name"),
                            max_length=255,
                            blank=True,
                            null=True)
    phone_number = models.CharField(_("Contact Number"),
                                     max_length=255,
                                     blank=True,
                                     null=True)
    verification_document = models.ImageField(
        null=True,
        upload_to='staff/verifications',
        blank=True,
        validators=[limit_size, validate_image_file_extension])
    pan = models.CharField(_("PAN Number"),
                           max_length=100,
                           unique=True,
                           blank=True,
                           null=True)

    assigned_salary = models.DecimalField(max_digits=10,
                                          decimal_places=2,
                                          default=Decimal("0.00"))

    address = models.TextField(_("Address"), blank=True, null=True)
    enrollment_date = models.DateField(_("Enrollment Date"), blank=True, null=True)

    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)


# Vehicle and GatePass models are now in statements.models.logistics.
# This file primarily holds the Staff model and other support structures.
