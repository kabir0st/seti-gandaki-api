# Frontend Guide: HRM Attendance Feature

This document outlines how to interact with the HRM Attendance API endpoints.

## Authentication

All endpoints require Bearer Token authentication. The token should be included in the `Authorization` header:

`Authorization: Bearer <your_access_token>`

## API Endpoints

The base URL for the attendance API is `/api/hrm/attendances/`.

### 1. List Attendances

-   **Endpoint**: `GET /api/hrm/attendances/`
-   **Description**: Retrieves a paginated list of attendance records.
-   **Permissions**: Authenticated users. Staff users can see all records; non-staff users might have restrictions based on future configurations (currently all authenticated users see all).
-   **Query Parameters (Filtering & Ordering)**:
    -   `page` (integer): Page number for pagination.
    -   `page_size` (integer): Number of items per page.
    -   `staff__id` (integer): Filter by staff ID.
        -   Example: `/api/hrm/attendances/?staff__id=5`
    -   `staff__name` (string): Filter by staff name (case-insensitive, contains).
        -   Example: `/api/hrm/attendances/?staff__name=John`
    -   `date` (YYYY-MM-DD): Filter by exact date.
        -   Example: `/api/hrm/attendances/?date=2024-05-28`
    -   `date_after` (YYYY-MM-DD): Filter for dates after (and including) the specified date. (Uses `date__gte`)
        -   Example: `/api/hrm/attendances/?date_after=2024-05-01`
    -   `date_before` (YYYY-MM-DD): Filter for dates before (and including) the specified date. (Uses `date__lte`)
        -   Example: `/api/hrm/attendances/?date_before=2024-05-31`
    -   `date_range_after` (YYYY-MM-DD): Start of a date range. (Uses `date__range` in combination with `date_range_before`)
    -   `date_range_before` (YYYY-MM-DD): End of a date range.
        -   Example: `/api/hrm/attendances/?date_range_after=2024-05-01&date_range_before=2024-05-15`
    -   `status` (string): Filter by attendance status.
        -   Choices: `PRESENT`, `ABSENT`, `LEAVE`, `HOLIDAY`, `HALF_DAY`
        -   Example: `/api/hrm/attendances/?status=PRESENT`
    -   `status__in` (string): Filter by multiple statuses (comma-separated).
        -   Example: `/api/hrm/attendances/?status__in=PRESENT,LEAVE`
    -   `search` (string): Search across `staff__name` and `remarks`.
        -   Example: `/api/hrm/attendances/?search=urgent`
    -   `ordering` (string): Field to order by. Prepend `-` for descending order.
        -   Available fields: `date`, `staff__name`, `status`, `created_at`
        -   Example: `/api/hrm/attendances/?ordering=-date,staff__name`
-   **Success Response (200 OK)**:
    ```json
    {
        "count": 15,
        "next": "/api/hrm/attendances/?page=2",
        "previous": null,
        "results": [
            {
                "id": 1,
                "staff": {
                    "id": 101,
                    "name": "John Doe",
                    "phone_number": "john.doe@example.com", // Note: This was EmailField in model, might be phone
                    "verification_document": "/media/staff/verifications/doc.jpg",
                    "pan": "ABCDE1234F",
                    "assigned_salary": "50000.00",
                    "address": "123 Main St",
                    "updated_at": "2024-05-28T10:00:00Z"
                },
                "staff_id": 101, // Included for convenience, staff object has full details
                "date": "2024-05-28",
                "check_in_time": "09:00:00",
                "check_out_time": "17:00:00",
                "status": "PRESENT",
                "status_display": "Present",
                "remarks": "Completed all tasks.",
                "created_at": "2024-05-28T12:00:00Z",
                "updated_at": "2024-05-28T12:05:00Z"
            },
            // ... more attendance records
        ]
    }
    ```

### 2. Create Attendance Record

-   **Endpoint**: `POST /api/hrm/attendances/`
-   **Description**: Creates a new attendance record.
-   **Permissions**: Authenticated staff users.
-   **Request Body**:
    ```json
    {
        "staff_id": 101, // Required: ID of the staff member
        "date": "2024-05-29", // Required: Date of attendance
        "check_in_time": "09:05:00", // Optional
        "check_out_time": "17:30:00", // Optional
        "status": "PRESENT", // Required: Choices - PRESENT, ABSENT, LEAVE, HOLIDAY, HALF_DAY
        "remarks": "Arrived a bit late." // Optional
    }
    ```
-   **Success Response (201 Created)**:
    ```json
    {
        "id": 2,
        "staff": {
            "id": 101,
            "name": "John Doe",
            // ... other staff details
        },
        "staff_id": 101,
        "date": "2024-05-29",
        "check_in_time": "09:05:00",
        "check_out_time": "17:30:00",
        "status": "PRESENT",
        "status_display": "Present",
        "remarks": "Arrived a bit late.",
        "created_at": "2024-05-29T08:00:00Z",
        "updated_at": "2024-05-29T08:00:00Z"
    }
    ```
-   **Error Response (400 Bad Request)**:
    -   If a record for the same staff and date already exists:
        ```json
        {
            "detail": "Attendance for John Doe on 2024-05-29 already exists."
        }
        ```
    -   For other validation errors (e.g., missing required fields):
        ```json
        {
            "staff_id": ["This field is required."],
            "date": ["Date has wrong format. Use one of these formats instead: YYYY-MM-DD."]
        }
        ```

### 3. Retrieve Attendance Record

-   **Endpoint**: `GET /api/hrm/attendances/{id}/`
-   **Description**: Retrieves a specific attendance record by its ID.
-   **Permissions**: Authenticated users.
-   **Success Response (200 OK)**:
    ```json
    {
        "id": 1,
        "staff": {
            "id": 101,
            "name": "John Doe",
            // ... other staff details
        },
        "staff_id": 101,
        "date": "2024-05-28",
        "check_in_time": "09:00:00",
        "check_out_time": "17:00:00",
        "status": "PRESENT",
        "status_display": "Present",
        "remarks": "Completed all tasks.",
        "created_at": "2024-05-28T12:00:00Z",
        "updated_at": "2024-05-28T12:05:00Z"
    }
    ```
-   **Error Response (404 Not Found)**: If the record does not exist.

### 4. Update Attendance Record (Full Update)

-   **Endpoint**: `PUT /api/hrm/attendances/{id}/`
-   **Description**: Fully updates an existing attendance record. All fields must be provided.
-   **Permissions**: Authenticated staff users.
-   **Request Body**:
    ```json
    {
        "staff_id": 101,
        "date": "2024-05-28",
        "check_in_time": "09:00:00",
        "check_out_time": "17:05:00", // Updated
        "status": "PRESENT",
        "remarks": "Completed all tasks. Stayed a bit late." // Updated
    }
    ```
-   **Success Response (200 OK)**:
    ```json
    {
        "id": 1,
        "staff": {
            "id": 101,
            "name": "John Doe",
            // ... other staff details
        },
        "staff_id": 101,
        "date": "2024-05-28",
        "check_in_time": "09:00:00",
        "check_out_time": "17:05:00",
        "status": "PRESENT",
        "status_display": "Present",
        "remarks": "Completed all tasks. Stayed a bit late.",
        "created_at": "2024-05-28T12:00:00Z",
        "updated_at": "2024-05-28T14:00:00Z" // updated_at will change
    }
    ```
-   **Error Response (400 Bad Request)**: If validation fails (e.g., trying to change staff/date to a combination that already exists for another record).

### 5. Partially Update Attendance Record

-   **Endpoint**: `PATCH /api/hrm/attendances/{id}/`
-   **Description**: Partially updates an existing attendance record. Only include fields to be updated.
-   **Permissions**: Authenticated staff users.
-   **Request Body** (Example: updating only remarks and check_out_time):
    ```json
    {
        "check_out_time": "17:10:00",
        "remarks": "Updated remarks for PATCH."
    }
    ```
-   **Success Response (200 OK)**:
    ```json
    {
        "id": 1,
        "staff": {
            "id": 101,
            "name": "John Doe",
            // ... other staff details
        },
        "staff_id": 101,
        "date": "2024-05-28",
        "check_in_time": "09:00:00", // Unchanged
        "check_out_time": "17:10:00", // Updated
        "status": "PRESENT", // Unchanged
        "status_display": "Present",
        "remarks": "Updated remarks for PATCH.", // Updated
        "created_at": "2024-05-28T12:00:00Z",
        "updated_at": "2024-05-28T14:05:00Z" // updated_at will change
    }
    ```

### 6. Delete Attendance Record

-   **Endpoint**: `DELETE /api/hrm/attendances/{id}/`
-   **Description**: Deletes a specific attendance record.
-   **Permissions**: Authenticated staff users.
-   **Success Response (204 No Content)**: Empty response indicating successful deletion.
-   **Error Response (404 Not Found)**: If the record does not exist.

## Status Choices

The `status` field can have one of the following values:

-   `PRESENT`
-   `ABSENT`
-   `LEAVE`
-   `HOLIDAY`
-   `HALF_DAY`

The API will also return a `status_display` field which provides the human-readable version of the status (e.g., "Present", "On Leave").

## Notes

-   The `staff` object in responses contains detailed information about the staff member. For `POST`, `PUT`, and `PATCH` requests, you only need to provide the `staff_id`.
-   The `created_at` and `updated_at` fields are read-only and automatically managed by the server.
-   Ensure date and time formats are correct as specified.