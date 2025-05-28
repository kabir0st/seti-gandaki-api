from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from statements.models.support import Staff
from core.utils.models.abstract import DefaultModel # Changed TimeStampedModel to DefaultModel

class AttendanceChoice(models.TextChoices):
    PRESENT = "PRESENT", _("Present")
    ABSENT = "ABSENT", _("Absent")
    LEAVE = "LEAVE", _("On Leave")
    HOLIDAY = "HOLIDAY", _("Holiday")
    HALF_DAY = "HALF_DAY", _("Half Day")


class Attendance(DefaultModel): # Changed TimeStampedModel to DefaultModel
    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name=_("Staff")
    )
    date = models.DateField(_("Date"), default=timezone.now)
    check_in_time = models.TimeField(_("Check-in Time"), null=True, blank=True)
    check_out_time = models.TimeField(_("Check-out Time"), null=True, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=AttendanceChoice.choices,
        default=AttendanceChoice.PRESENT
    )
    remarks = models.TextField(_("Remarks"), blank=True, null=True)

    class Meta:
        verbose_name = _("Attendance")
        verbose_name_plural = _("Attendances")
        unique_together = ('staff', 'date') # Each staff can only have one attendance record per day
        ordering = ['-date', 'staff__name']

    def __str__(self):
        return f"{self.staff.name} - {self.date} ({self.get_status_display()})"