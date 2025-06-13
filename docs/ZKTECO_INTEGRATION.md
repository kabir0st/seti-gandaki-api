# ZKTeco K40 Pro Integration

This document describes the integration with ZKTeco K40 Pro attendance device for automatic attendance tracking.

## Overview

The system automatically processes attendance data when employees scan their fingerprints on the ZKTeco K40 Pro device. The integration includes:

- Real-time attendance data processing via heartbeat endpoint
- Automatic check-in/check-out detection
- Staff mapping via device user IDs
- Manual sync functionality
- Device status monitoring

## Setup

### 1. Database Migration

Run the migrations to create the necessary database tables:

```bash
cd src
python manage.py migrate
```

### 2. Staff Device ID Mapping

Each staff member needs to be assigned a device user ID that matches their ID in the ZKTeco device:

```python
# Via Django admin or API
staff = Staff.objects.get(id=1)
staff.device_id = "2"  # This should match the user ID in ZKTeco device
staff.save()
```

### 3. Device Configuration

Configure your ZKTeco K40 Pro device to send data to your server:

- **Push URL**: `http://your-server.com/iclock/cdata`
- **Heartbeat URL**: `http://your-server.com/iclock/getrequest`
- **Protocol**: HTTP POST

## API Endpoints

### Device Management APIs

All device management APIs require authentication.

#### 1. Sync Device Attendance

**POST** `/hrm/device/sync/`

Manually sync all attendance logs from the ZKTeco device.

```json
{
    "device_ip": "192.168.1.100",
    "device_port": 80
}
```

**Response:**
```json
{
    "message": "Sync completed successfully",
    "processed_logs": 15,
    "new_attendances": 8,
    "timestamp": "2025-06-14T10:30:00Z"
}
```

#### 2. Check Device Status

**GET** `/hrm/device/status/?device_ip=192.168.1.100&device_port=80`

Check if the ZKTeco device is online and responsive.

**Response:**
```json
{
    "online": true,
    "device_info": "ZKTeco K40 Pro v1.2.3",
    "last_check": "2025-06-14T10:30:00Z",
    "error": null
}
```

#### 3. View Device Logs

**GET** `/hrm/device/logs/`

View processed device attendance logs with optional filters.

**Query Parameters:**
- `staff_id`: Filter by staff ID
- `date_from`: Filter from date (YYYY-MM-DD)
- `date_to`: Filter to date (YYYY-MM-DD)
- `is_processed`: Filter by processing status (true/false)
- `limit`: Limit results (default: 100)

#### 4. Process Raw Data

**POST** `/hrm/device/process-raw/`

Manually process raw attendance data string.

```json
{
    "raw_data": "2\t2025-06-14 00:55:35\t0\t1\t0\t0\t0\t0\t0\t0"
}
```

#### 5. Staff Device Mapping

**GET** `/hrm/device/staff-mapping/`

View all staff members and their device ID mappings.

#### 6. Update Staff Device ID

**POST** `/hrm/device/update-staff-device/`

Update a staff member's device ID mapping.

```json
{
    "staff_id": 1,
    "device_id": "2"
}
```

## Data Format

### ZKTeco Attendance Log Format

The ZKTeco device sends attendance data in the following format:

```
UserID    Timestamp            Status  Verified  WorkCode  Reserved...
2         2025-06-14 00:55:35   0       1         0         0 0 0 0 0
```

**Field Meanings:**
- **UserID**: Device user ID (maps to Staff.device_id)
- **Timestamp**: Date and time of attendance
- **Status**: 
  - `0` = Check-In
  - `1` = Check-Out
  - `2` = Break-Out
  - `3` = Break-In
- **Verified**: Verification method
  - `0` = Password
  - `1` = Fingerprint
  - `2` = Card
  - `3` = Face
- **WorkCode**: Optional work code (usually 0)

## Management Commands

### Sync Device Data

```bash
# Sync attendance data from device
python manage.py sync_zkteco_device --device-ip 192.168.1.100

# Check device status only
python manage.py sync_zkteco_device --device-ip 192.168.1.100 --check-status

# List staff device mappings
python manage.py sync_zkteco_device --device-ip 192.168.1.100 --list-staff
```

### Test with Sample Data

```bash
# Create test staff members
python manage.py test_zkteco_data --create-test-staff

# Test data processing
python manage.py test_zkteco_data
```

## Models

### DeviceAttendanceLog

Stores raw attendance logs from the ZKTeco device:

- `device_user_id`: User ID from device
- `staff`: Foreign key to Staff (if mapped)
- `timestamp`: Attendance timestamp
- `attendance_status`: Check-in/out status
- `verification_method`: How user was verified
- `is_processed`: Whether log has been processed into attendance
- `raw_data`: Original raw data string

### Attendance (Enhanced)

The existing Attendance model automatically gets updated when device logs are processed:

- `check_in_time`: Automatically set from first check-in of the day
- `check_out_time`: Automatically set from last check-out of the day
- `status`: Automatically set to PRESENT when device data is received

## Workflow

1. **Employee scans fingerprint** on ZKTeco K40 Pro device
2. **Device sends data** to `/iclock/cdata` endpoint via HTTP POST
3. **System processes data**:
   - Parses attendance log format
   - Finds staff by device_id
   - Creates DeviceAttendanceLog entry
   - Updates/creates Attendance record
4. **Attendance is automatically marked** as present with check-in/out times

## Troubleshooting

### Common Issues

1. **No staff found for device user ID**
   - Ensure Staff.device_id matches the user ID in ZKTeco device
   - Check device user management in ZKTeco software

2. **Device not sending data**
   - Verify network connectivity
   - Check device push URL configuration
   - Ensure firewall allows HTTP traffic

3. **Timestamp issues**
   - Verify device time zone settings
   - Check Django TIME_ZONE setting

### Logs

Check Django logs for detailed error information:

```python
import logging
logger = logging.getLogger('hrm.apis.device')
```

## Security Considerations

- The heartbeat endpoint (`/iclock/cdata`) is exempt from CSRF protection for device compatibility
- Consider using HTTPS in production
- Implement IP whitelisting for device endpoints if needed
- Regular backup of attendance data is recommended

## Future Enhancements

- Support for multiple ZKTeco devices
- Real-time notifications for attendance events
- Advanced reporting and analytics
- Integration with payroll systems
- Mobile app for attendance viewing