from decimal import Decimal
from django.core.validators import validate_image_file_extension
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from datetime import datetime, date

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
    device_id = models.CharField(_("Device User ID"),
                                max_length=10,
                                unique=True,
                                blank=True,
                                null=True,
                                help_text=_("ZKTeco device user ID for attendance tracking"))

    assigned_salary = models.DecimalField(max_digits=10,
                                          decimal_places=2,
                                          default=Decimal("0.00"))

    address = models.TextField(_("Address"), blank=True, null=True)
    enrollment_date = models.DateField(_("Enrollment Date"), blank=True, null=True)

    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    def __str__(self):
        return self.name or f"Staff #{self.id}"

    def get_office_attendance_dates(self, start_date=None, end_date=None, attendance_type=None):
        """
        Get all dates when staff came to office with optional filters
        
        Args:
            start_date (date, optional): Filter from this date
            end_date (date, optional): Filter until this date
            attendance_type (str, optional): Filter by attendance type ('CHECK_IN' or 'CHECK_OUT')
        
        Returns:
            QuerySet: Attendance records ordered by date and time
        """
        # Import here to avoid circular imports
        from hrm.models.attendance import Attendance
        
        queryset = self.attendances.all()
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
            
        if attendance_type:
            queryset = queryset.filter(attendance_type=attendance_type)
            
        return queryset.order_by('date', 'time')

    def get_office_days(self, start_date=None, end_date=None):
        """
        Get unique dates when staff came to office (had any attendance record)
        
        Args:
            start_date (date, optional): Filter from this date
            end_date (date, optional): Filter until this date
        
        Returns:
            QuerySet: Distinct dates when staff had attendance
        """
        queryset = self.get_office_attendance_dates(start_date=start_date, end_date=end_date)
        return queryset.values_list('date', flat=True).distinct().order_by('date')

    def get_check_ins(self, start_date=None, end_date=None):
        """
        Get all check-in records for the staff
        
        Args:
            start_date (date, optional): Filter from this date
            end_date (date, optional): Filter until this date
        
        Returns:
            QuerySet: Check-in attendance records
        """
        return self.get_office_attendance_dates(
            start_date=start_date,
            end_date=end_date,
            attendance_type='CHECK_IN'
        )

    def get_check_outs(self, start_date=None, end_date=None):
        """
        Get all check-out records for the staff
        
        Args:
            start_date (date, optional): Filter from this date
            end_date (date, optional): Filter until this date
        
        Returns:
            QuerySet: Check-out attendance records
        """
        return self.get_office_attendance_dates(
            start_date=start_date,
            end_date=end_date,
            attendance_type='CHECK_OUT'
        )

    def get_daily_attendance_summary(self, target_date=None):
        """
        Get attendance summary for a specific date
        
        Args:
            target_date (date, optional): Date to get summary for. Defaults to today.
        
        Returns:
            dict: Summary containing check-in and check-out times, total records
        """
        if target_date is None:
            target_date = date.today()
            
        daily_attendance = self.attendances.filter(date=target_date).order_by('time')
        
        check_ins = daily_attendance.filter(attendance_type='CHECK_IN')
        check_outs = daily_attendance.filter(attendance_type='CHECK_OUT')
        
        return {
            'date': target_date,
            'total_records': daily_attendance.count(),
            'check_ins': list(check_ins),
            'check_outs': list(check_outs),
            'first_check_in': check_ins.first(),
            'last_check_out': check_outs.last(),
        }

    class Meta:
        verbose_name = _("Staff")
        verbose_name_plural = _("Staff")


# Vehicle and GatePass models are now in statements.models.logistics.
# This file primarily holds the Staff model and other support structures.
