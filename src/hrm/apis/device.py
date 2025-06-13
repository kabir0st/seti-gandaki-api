from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
import datetime
import logging
import requests
from typing import Optional

from hrm.models.attendance import (
    Attendance, AttendanceTypeChoice, VerificationChoice
)
from statements.models.support import Staff

logger = logging.getLogger(__name__)


@csrf_exempt
def heartbeat(request):
    """
    ZKTeco K40 Pro heartbeat endpoint that receives attendance data
    when someone scans their fingerprint
    """
    if request.method == "POST":
        raw_data = request.body.decode('utf-8')
        logger.info(f"Attendance data received from ZKTeco device:\n{raw_data}")
        
        try:
            with transaction.atomic():
                print('get info', raw_data)
                processed_attendances = process_attendance_data(raw_data)
                logger.info(f"Successfully processed {len(processed_attendances)} attendance records")
        except Exception as e:
            logger.error(f"Error processing attendance data: {str(e)}")
            return HttpResponse("ERROR", status=500)

        return HttpResponse("OK")

    return HttpResponse("OK")


def process_attendance_data(raw_data: str) -> list:
    """
    Process raw attendance data from ZKTeco device and create attendance records
    Each line represents a check-in or check-out event
    """
    processed_attendances = []
    lines = raw_data.strip().splitlines()
    
    for line in lines:
        if not line.strip():
            continue
            
        # Split by tabs first, then by spaces if no tabs
        parts = line.split('\t') if '\t' in line else line.split()
        
        if len(parts) >= 3:
            try:
                device_user_id = parts[0]
                # Handle timestamp - it should be in parts[1] as "YYYY-MM-DD HH:MM:SS"
                timestamp_str = parts[1]
                attendance_status = parts[2] if len(parts) > 2 else "0"
                verification_method_code = parts[3] if len(parts) > 3 else "1"  # Default to fingerprint

                # Parse timestamp
                try:
                    timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    # Make timezone aware
                    if timezone.is_naive(timestamp):
                        timestamp = timezone.make_aware(timestamp)
                except ValueError as e:
                    logger.error(f"Invalid timestamp format '{timestamp_str}': {e}")
                    continue

                # Find staff by device_id
                staff = None
                try:
                    staff = Staff.objects.get(device_id=device_user_id)
                except Staff.DoesNotExist:
                    logger.warning(f"No staff found with device_id: {device_user_id}")
                    continue  # Skip if no staff found

                # Map verification method code to choice
                verification_method_map = {
                    "0": VerificationChoice.PASSWORD,
                    "1": VerificationChoice.FINGERPRINT,
                    "2": VerificationChoice.CARD,
                    "3": VerificationChoice.FACE,
                }
                verification_method = verification_method_map.get(
                    verification_method_code, VerificationChoice.FINGERPRINT
                )

                # Determine attendance type based on status code
                # Common ZKTeco status codes: 0=Check In, 1=Check Out, 2=Break Out, 3=Break In, etc.
                attendance_type = AttendanceTypeChoice.CHECK_IN
                if attendance_status in ["1", "3"]:  # Check out or break in
                    attendance_type = AttendanceTypeChoice.CHECK_OUT

                # Create attendance record for this specific event
                attendance = Attendance.objects.create(
                    staff=staff,
                    date=timestamp.date(),
                    time=timestamp.time(),
                    attendance_type=attendance_type,
                    verification_method=verification_method,
                    remarks=f'Device event - Status: {attendance_status}, Raw: {line}'
                )

                processed_attendances.append(attendance)
                logger.info(f"Processed: {staff.name}, Date: {timestamp.date()}, Time: {timestamp.time()}, "
                          f"Type: {attendance_type}, Status: {attendance_status}, Verified by: {verification_method}")

            except Exception as e:
                logger.error(f"Error processing line '{line}': {str(e)}")
                continue

    return processed_attendances


def fetch_all_device_logs(device_ip: str, device_port: int = 80, timeout: int = 30) -> Optional[str]:
    """
    Fetch all attendance logs from ZKTeco K40 Pro device
    
    Args:
        device_ip: IP address of the ZKTeco device
        device_port: Port number (default 80)
        timeout: Request timeout in seconds
    
    Returns:
        Raw attendance log data as string, or None if failed
    """
    try:
        # ZKTeco devices typically use HTTP GET to fetch logs
        url = f"http://{device_ip}:{device_port}/iclock/cdata"
        
        # Some devices require specific headers
        headers = {
            'User-Agent': 'ZKTeco-Client',
            'Content-Type': 'text/plain'
        }
        
        logger.info(f"Fetching logs from ZKTeco device at {device_ip}:{device_port}")
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        raw_data = response.text
        logger.info(f"Successfully fetched {len(raw_data)} bytes of log data")
        
        return raw_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch logs from device {device_ip}:{device_port}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching device logs: {str(e)}")
        return None


def sync_device_logs(device_ip: str, device_port: int = 80) -> dict:
    """
    Fetch and sync all logs from ZKTeco device with database
    
    Args:
        device_ip: IP address of the ZKTeco device
        device_port: Port number (default 80)
    
    Returns:
        Dictionary with sync results
    """
    result = {
        'success': False,
        'processed_attendances': 0,
        'updated_attendances': 0,
        'errors': []
    }
    
    try:
        # Fetch raw data from device
        raw_data = fetch_all_device_logs(device_ip, device_port)
        
        if not raw_data:
            result['errors'].append("Failed to fetch data from device")
            return result
        
        # Process the fetched data
        with transaction.atomic():
            processed_attendances = process_attendance_data(raw_data)
            result['processed_attendances'] = len(processed_attendances)
            result['updated_attendances'] = len(processed_attendances)
            result['success'] = True
            
        logger.info(f"Sync completed: {result['processed_attendances']} attendance records processed")
        
    except Exception as e:
        error_msg = f"Error during sync: {str(e)}"
        logger.error(error_msg)
        result['errors'].append(error_msg)
    
    return result


def get_device_status(device_ip: str, device_port: int = 80) -> dict:
    """
    Check ZKTeco device status and basic information
    
    Args:
        device_ip: IP address of the ZKTeco device
        device_port: Port number (default 80)
    
    Returns:
        Dictionary with device status information
    """
    status = {
        'online': False,
        'device_info': None,
        'last_check': timezone.now(),
        'error': None
    }
    
    try:
        url = f"http://{device_ip}:{device_port}/iclock/getrequest"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            status['online'] = True
            status['device_info'] = response.text[:200]  # First 200 chars
        else:
            status['error'] = f"HTTP {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        status['error'] = str(e)
    except Exception as e:
        status['error'] = f"Unexpected error: {str(e)}"
    
    return status