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
    # entry_time and exit_time are moved to GatePassMovement
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
    # This is the issue time
    created_at = models.DateTimeField(_("Issued At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At Record"), auto_now=True)

    class Meta:
        verbose_name = _("Gate Pass")
        verbose_name_plural = _("Gate Passes")
        ordering = ["-created_at"]  # Order by issue time

    def __str__(self):
        return (
            f"Gate Pass for {self.vehicle or self.license_plate} issued at "
            f"{self.created_at.strftime('%Y-%m-%d %H:%M')}")


class GatePassMovement(models.Model):
    gate_pass = models.ForeignKey(GatePass,
                                  on_delete=models.CASCADE,
                                  related_name='movements',
                                  verbose_name=_("Gate Pass"))
    # For company vehicles, first movement is an exit, then entry,
    # then exit, etc.
    # For external vehicles, first movement is an entry, then exit,
    # then entry, etc.
    exit_time = models.DateTimeField(_("Exit Time"), blank=True, null=True)
    entry_time = models.DateTimeField(_("Entry Time"), blank=True, null=True)
    # Potentially add: security_personnel,
    # specific_remarks_for_movement

    created_at = models.DateTimeField(_("Recorded At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Gate Pass Movement")
        verbose_name_plural = _("Gate Pass Movements")
        ordering = ["gate_pass", "-created_at"]

    def __str__(self):
        movement_type = "Exit" if self.exit_time else "Entry"
        movement_time = self.exit_time or self.entry_time
        vehicle_id = self.gate_pass.vehicle or self.gate_pass.license_plate
        time_str = (movement_time.strftime('%Y-%m-%d %H:%M')
                    if movement_time else 'N/A')
        return f"{movement_type} for {vehicle_id} at {time_str}"


class TripLog(models.Model):
    gate_pass = models.ForeignKey(GatePass,
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
