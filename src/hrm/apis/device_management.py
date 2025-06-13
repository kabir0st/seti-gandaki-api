from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
import logging

from hrm.apis.device import sync_device_logs, get_device_status, fetch_all_device_logs, process_attendance_data
from hrm.models.attendance import Attendance
from statements.models.support import Staff

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sync_device_attendance(request):
    """
    API endpoint to manually sync attendance logs from ZKTeco device
    
    POST data:
    {
        "device_ip": "192.168.1.100",
        "device_port": 80  // optional, defaults to 80
    }
    """
    device_ip = '192.168.1.201'
    device_port = 80
    
    if not device_ip:
        return Response(
            {'error': 'device_ip is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        result = sync_device_logs(device_ip, device_port)
        
        if result['success']:
            return Response({
                'message': 'Sync completed successfully',
                'processed_attendances': result['processed_attendances'],
                'updated_attendances': result['updated_attendances'],
                'timestamp': timezone.now()
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Sync failed',
                'errors': result['errors']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error in sync_device_attendance: {str(e)}")
        return Response(
            {'error': f'Sync failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def device_logs(request):
    """
    API endpoint to view attendance records from device
    
    Query parameters:
    - staff_id: Filter by staff ID (optional)
    - date_from: Filter from date (YYYY-MM-DD) (optional)
    - date_to: Filter to date (YYYY-MM-DD) (optional)
    - attendance_type: Filter by attendance type (optional)
    """
    # Get attendance records that have device-related remarks (indicating they came from device)
    queryset = Attendance.objects.filter(
        remarks__icontains='Device event'
    ).select_related('staff')
    
    # Apply filters
    staff_id = request.query_params.get('staff_id')
    if staff_id:
        queryset = queryset.filter(staff_id=staff_id)
    
    date_from = request.query_params.get('date_from')
    if date_from:
        queryset = queryset.filter(date__gte=date_from)
    
    date_to = request.query_params.get('date_to')
    if date_to:
        queryset = queryset.filter(date__lte=date_to)
    
    attendance_type = request.query_params.get('attendance_type')
    if attendance_type:
        queryset = queryset.filter(attendance_type=attendance_type)
    
    # Order by date and time
    queryset = queryset.order_by('-date', '-time')
    
    # Limit results
    limit = int(request.query_params.get('limit', 100))
    queryset = queryset[:limit]
    
    logs_data = []
    for attendance in queryset:
        logs_data.append({
            'id': attendance.id,
            'staff_name': attendance.staff.name,
            'staff_id': attendance.staff.id,
            'date': attendance.date,
            'time': attendance.time,
            'attendance_type': attendance.get_attendance_type_display(),
            'verification_method': attendance.get_verification_method_display(),
            'remarks': attendance.remarks,
            'created_at': attendance.created_at
        })
    
    return Response({
        'logs': logs_data,
        'count': len(logs_data)
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_raw_data(request):
    """
    API endpoint to manually process raw attendance data
    
    POST data:
    {
        "raw_data": "2\t2025-06-14 00:55:35\t0\t1\t0\t0\t0\t0\t0\t0"
    }
    """
    raw_data = request.data.get('raw_data')
    
    if not raw_data:
        return Response(
            {'error': 'raw_data is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        processed_attendances = process_attendance_data(raw_data)
        
        attendance_info = []
        for attendance in processed_attendances:
            attendance_info.append({
                'staff_name': attendance.staff.name,
                'staff_id': attendance.staff.id,
                'date': attendance.date,
                'time': attendance.time,
                'attendance_type': attendance.get_attendance_type_display(),
                'verification_method': attendance.get_verification_method_display(),
                'remarks': attendance.remarks
            })
        
        return Response({
            'message': f'Successfully processed {len(processed_attendances)} attendance records',
            'attendances': attendance_info
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error processing raw data: {str(e)}")
        return Response(
            {'error': f'Failed to process data: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_device_mapping(request):
    """
    API endpoint to view staff and their device ID mappings
    """
    staff_with_devices = Staff.objects.filter(device_id__isnull=False).exclude(device_id='')
    
    mappings = []
    for staff in staff_with_devices:
        mappings.append({
            'staff_id': staff.id,
            'staff_name': staff.name,
            'device_id': staff.device_id,
            'phone_number': staff.phone_number,
            'enrollment_date': staff.enrollment_date
        })
    
    return Response({
        'mappings': mappings,
        'count': len(mappings)
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_staff_device_id(request):
    """
    API endpoint to update staff device ID mapping
    
    POST data:
    {
        "staff_id": 1,
        "device_id": "2"
    }
    """
    staff_id = request.data.get('staff_id')
    device_id = request.data.get('device_id')
    
    if not staff_id or not device_id:
        return Response(
            {'error': 'staff_id and device_id are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        staff = Staff.objects.get(id=staff_id)
        
        # Check if device_id is already used by another staff
        existing_staff = Staff.objects.filter(device_id=device_id).exclude(id=staff_id).first()
        if existing_staff:
            return Response(
                {'error': f'Device ID {device_id} is already assigned to {existing_staff.name}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        staff.device_id = device_id
        staff.save()
        
        return Response({
            'message': f'Successfully updated device ID for {staff.name}',
            'staff_name': staff.name,
            'device_id': device_id
        }, status=status.HTTP_200_OK)
        
    except Staff.DoesNotExist:
        return Response(
            {'error': 'Staff not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error updating staff device ID: {str(e)}")
        return Response(
            {'error': f'Failed to update: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )