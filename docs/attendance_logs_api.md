# Attendance Logs API Documentation

## Overview
The Attendance Logs API endpoint provides detailed attendance records for a specific staff member within a date range, along with calculated working hours and attendance statistics.

## Endpoint
```
GET /api/hrm/attendances/logs/
```

## Query Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `staff_id` | integer | Yes | ID of the staff member | `6` |
| `date_from` | string | No | Start date in YYYY-MM-DD format | `2024-01-01` |
| `date_to` | string | No | End date in YYYY-MM-DD format | `2024-01-31` |

## Response Format

### Success Response (200 OK)

#### Response Headers
The response includes summary statistics in custom headers:

| Header | Description | Example |
|--------|-------------|---------|
| `X-Total-Days-Present` | Number of days the staff member was present | `22` |
| `X-Total-Working-Hours` | Total working hours calculated | `176.50` |
| `X-Average-Hours-Per-Day` | Average working hours per day | `8.02` |
| `X-Date-Range` | Date range queried | `2024-01-01 to 2024-01-31` |
| `X-Staff-ID` | Staff ID queried | `6` |

#### Response Body
```json
{
  "count": 44,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "staff": {
        "id": 6,
        "name": "John Doe",
        "phone_number": "+1234567890"
      },
      "staff_id": 6,
      "date": "2024-01-01",
      "time": "09:00:00",
      "attendance_type": "CHECK_IN",
      "attendance_type_display": "Check In",
      "verification_method": "FINGERPRINT",
      "verification_method_display": "Fingerprint",
      "remarks": null,
      "created_at": "2024-01-01T09:00:00Z",
      "updated_at": "2024-01-01T09:00:00Z"
    },
    {
      "id": 2,
      "staff": {
        "id": 6,
        "name": "John Doe",
        "phone_number": "+1234567890"
      },
      "staff_id": 6,
      "date": "2024-01-01",
      "time": "17:30:00",
      "attendance_type": "CHECK_OUT",
      "attendance_type_display": "Check Out",
      "verification_method": "FINGERPRINT",
      "verification_method_display": "Fingerprint",
      "remarks": null,
      "created_at": "2024-01-01T17:30:00Z",
      "updated_at": "2024-01-01T17:30:00Z"
    }
  ],
  "summary": {
    "total_days_present": 22,
    "total_working_hours": 176.5,
    "average_hours_per_day": 8.02,
    "date_range": {
      "from": "2024-01-01",
      "to": "2024-01-31"
    },
    "staff_id": 6
  }
}
```

### Error Responses

#### 400 Bad Request - Missing staff_id
```json
{
  "error": "staff_id parameter is required"
}
```

#### 400 Bad Request - Invalid staff_id
```json
{
  "error": "staff_id must be a valid integer"
}
```

#### 400 Bad Request - Invalid date format
```json
{
  "error": "Invalid date_from format. Use YYYY-MM-DD"
}
```

#### 404 Not Found - No records found
```json
{
  "error": "No attendance records found for the specified criteria"
}
```

## Working Hours Calculation

The API calculates working hours using the following logic:

1. **Daily Grouping**: Attendance records are grouped by date
2. **Check-in/Check-out Pairing**: 
   - First check-in of the day is used as the start time
   - Last check-out of the day is used as the end time
3. **Default Times**: When only one type of record exists for a day:
   - If only check-in exists: assumes check-out at 5:00 PM
   - If only check-out exists: assumes check-in at 10:00 AM
4. **Working Hours**: Calculated as the difference between check-in and check-out times

## Example Usage

### Basic Query
```bash
GET /api/hrm/attendances/logs/?staff_id=6
```

### Query with Date Range
```bash
GET /api/hrm/attendances/logs/?staff_id=6&date_from=2024-01-01&date_to=2024-01-31
```

### Using cURL
```bash
curl -X GET "http://localhost:8000/api/hrm/attendances/logs/?staff_id=6&date_from=2024-01-01&date_to=2024-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

### Using Python requests
```python
import requests

url = "http://localhost:8000/api/hrm/attendances/logs/"
params = {
    "staff_id": 6,
    "date_from": "2024-01-01",
    "date_to": "2024-01-31"
}
headers = {
    "Authorization": "Bearer YOUR_TOKEN"
}

response = requests.get(url, params=params, headers=headers)
data = response.json()

# Access summary statistics from headers
total_days = response.headers.get('X-Total-Days-Present')
total_hours = response.headers.get('X-Total-Working-Hours')

# Or from response body
summary = data.get('summary', {})
print(f"Total working hours: {summary['total_working_hours']}")
```

## Notes

- The endpoint supports pagination for large result sets
- All times are returned in the server's timezone
- The summary statistics are included both in response headers and the response body
- Authentication is required to access this endpoint
- The endpoint is optimized for performance with proper database indexing on staff and date fields