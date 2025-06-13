from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from statements.models.support import Staff
from core.utils.models.abstract import DefaultModel


class AttendanceTypeChoice(models.TextChoices):
    CHECK_IN = "CHECK_IN", _("Check In")
    CHECK_OUT = "CHECK_OUT", _("Check Out")


class VerificationChoice(models.TextChoices):
    PASSWORD = "PASSWORD", _("Password")
    FINGERPRINT = "FINGERPRINT", _("Fingerprint")
    CARD = "CARD", _("Card")
    FACE = "FACE", _("Face")
    MANUAL = "MANUAL", _("Manual Entry")


class Attendance(DefaultModel):
    """
    Simplified attendance model - each record represents a single check-in or check-out event
    """
    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name=_("Staff")
    )
    date = models.DateField(_("Date"), default=timezone.localdate)
    time = models.TimeField(_("Time"), default=timezone.localtime)
    attendance_type = models.CharField(
        _("Type"),
        max_length=20,
        choices=AttendanceTypeChoice.choices,
        default=AttendanceTypeChoice.CHECK_IN
    )
    verification_method = models.CharField(
        _("Verification Method"),
        max_length=20,
        choices=VerificationChoice.choices,
        default=VerificationChoice.MANUAL
    )
    remarks = models.TextField(_("Remarks"), blank=True, null=True)

    class Meta:
        verbose_name = _("Attendance")
        verbose_name_plural = _("Attendances")
        ordering = ['-date', '-time']
        indexes = [
            models.Index(fields=['staff', 'date']),
            models.Index(fields=['date', 'attendance_type']),
        ]

    def __str__(self):
        return f"{self.staff.name} - {self.date} {self.time} ({self.get_attendance_type_display()})"