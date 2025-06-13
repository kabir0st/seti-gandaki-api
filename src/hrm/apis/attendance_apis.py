from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
import json
import logging

from hrm.models.attendance import Attendance
from hrm.serializers import AttendanceSerializer, ManualAttendanceSerializer
from core.utils.permissions import IsStaffOrReadOnly
from core.utils.viewsets import DefaultViewSet

# Set up logging for ZKTeco device requests
logger = logging.getLogger(__name__)

class AttendanceViewSet(DefaultViewSet):
    """
    API endpoint that allows attendances to be viewed or edited.
    Handles both manual and device-generated attendance records.
    """
    queryset = Attendance.objects.select_related('staff').all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'staff__id': ['exact'],
        'staff__name': ['icontains'],
        'date': ['exact', 'gte', 'lte', 'range'],
        'status': ['exact', 'in'],
        'source': ['exact', 'in'],
    }
    search_fields = ['staff__name', 'remarks']
    ordering_fields = ['date', 'staff__name', 'status', 'source', 'created_at']
    ordering = ['-date', 'staff__name']

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
        queryset = self.get_queryset().filter(source='MANUAL')
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
        queryset = self.get_queryset().filter(source='DEVICE')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """
        Get all related attendance records for a specific staff member on the same date
        (Since AttendanceLog model was removed, we show related attendance events)
        """
        attendance = self.get_object()
        # Get all attendance records for the same staff on the same date
        related_attendances = Attendance.objects.filter(
            staff=attendance.staff,
            date=attendance.date
        ).order_by('time')
        
        page = self.paginate_queryset(related_attendances)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(related_attendances, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get attendance summary statistics
        """
        queryset = self.get_queryset()
        
        # Apply filters
        filtered_queryset = self.filter_queryset(queryset)
        
        summary = {
            'total_records': filtered_queryset.count(),
            'manual_records': filtered_queryset.filter(source='MANUAL').count(),
            'device_records': filtered_queryset.filter(source='DEVICE').count(),
            'present': filtered_queryset.filter(status='PRESENT').count(),
            'absent': filtered_queryset.filter(status='ABSENT').count(),
            'leave': filtered_queryset.filter(status='LEAVE').count(),
            'holiday': filtered_queryset.filter(status='HOLIDAY').count(),
            'half_day': filtered_queryset.filter(status='HALF_DAY').count(),
        }
        
        return Response(summary)

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def zkteco_webhook(self, request):
        """
        DEPRECATED: Use the heartbeat endpoint instead.
        This endpoint is kept for backward compatibility.
        """
        try:
            # Log the incoming request
            logger.info("ZKTeco Pro K40 request received at deprecated webhook")
            logger.info(f"Request headers: {dict(request.headers)}")
            logger.info(f"Request data: {request.data}")
            logger.info(f"Request body: {request.body}")
            
            # Print to console for debugging
            print("=" * 50)
            print("ZKTeco Pro K40 Request Received (DEPRECATED ENDPOINT)")
            print("=" * 50)
            print(f"Method: {request.method}")
            print(f"Headers: {dict(request.headers)}")
            print(f"Content Type: {request.content_type}")
            print(f"Raw Body: {request.body}")
            
            # Try to parse JSON data if available
            if request.data:
                print(f"Parsed Data: {request.data}")
            
            # Try to parse raw body as JSON if request.data is empty
            if not request.data and request.body:
                try:
                    body_data = json.loads(request.body.decode('utf-8'))
                    print(f"JSON Body: {body_data}")
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    print(f"Could not parse body as JSON: {e}")
                    print(f"Raw body (first 500 chars): {request.body[:500]}")
            
            print("=" * 50)
            
            # Return success response
            return Response({
                'status': 'success',
                'message': 'ZKTeco Pro K40 data received successfully (please use /iclock/cdata endpoint)',
                'received_at': request.META.get('HTTP_DATE', 'Unknown'),
                'data_received': bool(request.data or request.body)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error processing ZKTeco Pro K40 request: {str(e)}")
            print(f"Error processing ZKTeco Pro K40 request: {str(e)}")
            
            return Response({
                'status': 'error',
                'message': f'Error processing request: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



