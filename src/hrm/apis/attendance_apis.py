from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
import json

from hrm.models.attendance import Attendance
from hrm.serializers import AttendanceSerializer, ManualAttendanceSerializer
from core.utils.permissions import IsStaffOrReadOnly
from core.utils.viewsets import DefaultViewSet
import django_filters


class AttendanceFilter(django_filters.FilterSet):
    created_at = django_filters.DateFromToRangeFilter()
    updated_at = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Attendance
        fields = "__all__"


class AttendanceViewSet(DefaultViewSet):
    """
    API endpoint that allows attendances to be viewed or edited.
    Handles both manual and device-generated attendance records.
    """
    queryset = Attendance.objects.select_related('staff').all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]
    filterset_fields = {
        'staff__id': ['exact'],
        'staff__name': ['icontains'],
        'date': ['exact', 'gte', 'lte', 'range'],
    }
    search_fields = ['staff__name', 'remarks']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Add any specific filtering for the user if needed
        return queryset

    def get_serializer_class(self):
        """
        Use ManualAttendanceSerializer for manual operations to prevent
        accidental modification of device-related fields
        """
        if self.action in ['create', 'update', 'partial_update']:
            return ManualAttendanceSerializer
        return AttendanceSerializer

    @action(detail=False, methods=['get'])
    def manual_only(self, request):
        """
        Get only manually created attendance records
        """
        queryset = self.get_queryset().filter(verification_method='MANUAL')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def device_only(self, request):
        """
        Get only device-generated attendance records
        """
        queryset = self.get_queryset().exclude(verification_method='MANUAL')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def logs(self, request):
        """
        Get attendance logs for a staff member within a date range
        Query parameters:
        - staff_id: Required - ID of the staff member
        - date_from: Optional - Start date (YYYY-MM-DD format)
        - date_to: Optional - End date (YYYY-MM-DD format)
        """
        from datetime import datetime, time, timedelta
        from django.db.models import Q

        # Get query parameters
        staff_id = request.query_params.get('staff_id')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        if not staff_id:
            return Response({'error': 'staff_id parameter is required'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Validate staff_id is a valid integer
        try:
            staff_id = int(staff_id)
        except ValueError:
            return Response({'error': 'staff_id must be a valid integer'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Build filter query
        filter_query = Q(staff_id=staff_id)

        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                filter_query &= Q(date__gte=date_from_obj)
            except ValueError:
                return Response(
                    {'error': 'Invalid date_from format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST)

        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                filter_query &= Q(date__lte=date_to_obj)
            except ValueError:
                return Response(
                    {'error': 'Invalid date_to format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST)

        # Apply class filterset first, then custom logic
        base_queryset = self.filter_queryset(self.get_queryset())
        attendances = base_queryset.filter(filter_query)

        if not attendances.exists():
            return Response(
                {
                    'error':
                    'No attendance records found for the specified criteria'
                },
                status=status.HTTP_404_NOT_FOUND)

        # Calculate statistics
        # Group attendances by date
        daily_attendances = {}
        for attendance in attendances:
            date_key = attendance.date
            if date_key not in daily_attendances:
                daily_attendances[date_key] = {
                    'check_in': None,
                    'check_out': None
                }

            if attendance.attendance_type == 'CHECK_IN':
                # Take the first check-in of the day
                if daily_attendances[date_key]['check_in'] is None:
                    daily_attendances[date_key]['check_in'] = attendance.time
            elif attendance.attendance_type == 'CHECK_OUT':
                # Take the last check-out of the day
                daily_attendances[date_key]['check_out'] = attendance.time

        # Calculate working hours and days
        total_working_hours = 0
        days_present = len(daily_attendances)

        # Default times for calculation
        default_check_in = time(10, 0)  # 10:00 AM
        default_check_out = time(17, 0)  # 5:00 PM

        for date_key, times in daily_attendances.items():
            check_in_time = times['check_in'] or default_check_in
            check_out_time = times['check_out'] or default_check_out

            # Calculate working hours for this day
            check_in_datetime = datetime.combine(date_key, check_in_time)
            check_out_datetime = datetime.combine(date_key, check_out_time)

            # Handle case where check_out is before check_in (shouldn't happen but just in case)
            if check_out_datetime > check_in_datetime:
                working_duration = check_out_datetime - check_in_datetime
                total_working_hours += working_duration.total_seconds(
                ) / 3600  # Convert to hours

        # Prepare response with pagination
        page = self.paginate_queryset(attendances)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(attendances, many=True)
            response = Response(serializer.data)
        summary_data = {}
        # Add summary statistics to response headers
        summary_data['Total-Days-Present'] = str(days_present)
        summary_data['Total-Working-Hours'] = f"{total_working_hours:.2f}"
        summary_data[
            'Average-Hours-Per-Day'] = f"{total_working_hours / days_present if days_present > 0 else 0:.2f}"
        summary_data[
            'Date-Range'] = f"{date_from or 'N/A'} to {date_to or 'N/A'}"
        summary_data['Staff-ID'] = str(staff_id)
        response['response-properties'] = summary_data

        # Also include summary in response body
        if hasattr(response, 'data') and isinstance(response.data, dict):
            response.data['summary'] = {
                'total_days_present':
                days_present,
                'total_working_hours':
                round(total_working_hours, 2),
                'average_hours_per_day':
                round(
                    total_working_hours /
                    days_present if days_present > 0 else 0, 2),
                'date_range': {
                    'from': date_from,
                    'to': date_to
                },
                'staff_id':
                staff_id
            }

        return response
