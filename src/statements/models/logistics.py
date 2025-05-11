from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from statements.models.purchase_invoice import PurchaseBill, Vehicle


class GatePass(models.Model):
    vehicle = models.ForeignKey(Vehicle,
                                on_delete=models.PROTECT,
                                null=True,
                                blank=True,
                                related_name='gate_passes',
                                verbose_name=_("Vehicle"))

    license_plate = models.CharField(_("License Plate"),
                                     max_length=20,
                                     null=True,
                                     blank=True)

    entry_time = models.DateTimeField(_("Entry Time"), auto_now_add=True)
    exit_time = models.DateTimeField(_("Exit Time"), blank=True, null=True)
    purpose = models.TextField(_("Purpose of Visit"), blank=True, null=True)

    driver_name = models.CharField(_("Driver's Name"),
                                   max_length=100,
                                   blank=True,
                                   null=True)
    driver_phone = models.CharField(_("Driver's Phone"),
                                    max_length=20,
                                    blank=True,
                                    null=True)

    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='issued_gate_passes',
        verbose_name=_("Issued By"),
        null=True,
        blank=True  # Could be system generated or anonymous
    )
    created_at = models.DateTimeField(_("Created At Record"),
                                      auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At Record"), auto_now=True)

    class Meta:
        verbose_name = _("Gate Pass")
        verbose_name_plural = _("Gate Passes")
        ordering = ["-entry_time"]

    def __str__(self):
        return (f"Gate Pass for {self.vehicle} at "
                f"{self.entry_time.strftime('%Y-%m-%d %H:%M')}")


class TripLog(models.Model):
    vehicle = models.ForeignKey(Vehicle,
                                on_delete=models.PROTECT,
                                related_name='trip_logs',
                                verbose_name=_("Vehicle"))
    for_purchase_bill = models.ForeignKey(PurchaseBill,
                                          on_delete=models.CASCADE,
                                          null=True,
                                          blank=True)
    purpose = models.TextField(_("Purpose of Trip"), blank=True, null=True)
    notes = models.TextField(_("Notes/Remarks"), blank=True, null=True)

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Trip Log")
        verbose_name_plural = _("Trip Logs")
        ordering = ["-created_at"]  # Was: "-start_time"

    def __str__(self):
        return f"Trip Log for {self.vehicle} (ID: {self.id})"
