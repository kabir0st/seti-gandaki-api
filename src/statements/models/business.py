from django.db import models
from django.utils.translation import gettext_lazy as _


class Business(models.Model):
    name = models.CharField(_("Business Name"), max_length=255)
    registration_number = models.CharField(_("Registration Number"),
                                           max_length=100,
                                           unique=True,
                                           blank=True,
                                           null=True)
    contact_person = models.CharField(_("Contact Person"),
                                      max_length=255,
                                      blank=True,
                                      null=True)
    contact_email = models.EmailField(_("Contact Email"),
                                      max_length=255,
                                      blank=True,
                                      null=True)
    phone_number = models.CharField(_("Phone Number"),
                                    max_length=255,
                                    blank=True,
                                    null=True)
    address = models.TextField(_("Address"), blank=True, null=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Business")
        verbose_name_plural = _("Businesses")
        ordering = ["name"]

    def __str__(self):
        return self.name
