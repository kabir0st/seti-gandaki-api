# Frontend Guide: Station and Fuel Ticket System

## 1. Introduction

This document provides guidance for frontend developers on integrating with the Petrol Station and Fuel Ticket management system. The system allows for the creation, tracking, and consumption of fuel tickets, which are used to authorize and record fuel dispensing at designated petrol stations.

## 2. Petrol Stations

Petrol stations are entities where fuel tickets can be consumed.

### 2.1. Model: `PetrolStation`

Key fields for a petrol station:

-   `id` (Integer, Primary Key)
-   `name` (String): Name of the petrol station.
-   `station_code` (String, 4 digits, Unique): A unique 4-digit code for the station.
-   `location_details` (String, Optional): Address or other location information.
-   `is_active` (Boolean): Indicates if the station is currently active.
-   `created_at` (DateTime)
-   `updated_at` (DateTime)

([View Model](src/hrm/models/fuel.py:9))

### 2.2. API Endpoints

Base URL: `/api/hrm/petrol-stations/`

([View API Code](src/hrm/apis/fuel_ticket_apis.py:16))

-   **`GET /api/hrm/petrol-stations/`**
    -   Description: Lists all active petrol stations.
    -   Permissions: Public (as per current code, `permission_classes` is commented out but defaults might apply).
    -   Response: Array of `PetrolStation` objects.
        ```json
        [
            {
                "id": 1,
                "name": "Main Street Fuel Stop",
                "station_code": "1001",
                "location_details": "123 Main St, Anytown",
                "is_active": true,
                "created_at": "2024-05-28T10:00:00Z",
                "updated_at": "2024-05-28T10:00:00Z"
            },
            // ... more stations
        ]
        ```

-   **`GET /api/hrm/petrol-stations/{id}/`**
    -   Description: Retrieves details of a specific petrol station by its database `id`.
    -   Permissions: Public.
    -   Response: A single `PetrolStation` object.

-   **`POST /api/hrm/petrol-stations/`**
    -   Description: Creates a new petrol station.
    -   Permissions: Likely Admin/Staff only (based on commented `IsAdminUser` permission).
    -   Request Body: `PetrolStation` object fields (e.g., `name`, `station_code`).
        ```json
        {
            "name": "New City Gas",
            "station_code": "1002",
            "location_details": "456 New City Ave"
        }
        ```
    -   Response: The created `PetrolStation` object with its `id`.

-   **`PUT /api/hrm/petrol-stations/{id}/`**
    -   Description: Updates an existing petrol station.
    -   Permissions: Likely Admin/Staff only.
    -   Request Body: Fields to update.

-   **`DELETE /api/hrm/petrol-stations/{id}/`**
    -   Description: Deletes a petrol station.
    -   Permissions: Likely Admin/Staff only.

### 2.3. Frontend Usage

-   Displaying a list of petrol stations (e.g., in a dropdown menu when a fuel ticket is being marked as consumed).
-   Admin interfaces for managing petrol station records.

## 3. Fuel Tickets

Fuel tickets authorize a specific quantity and type of fuel to be dispensed.

### 3.1. Model: `FuelTicket`

Key fields for a fuel ticket:

-   `id` (Integer, Primary Key - Database ID)
-   `ticket_id` (UUID, Unique, Auto-generated): Publicly visible ticket identifier.
-   `dispatched_by` (User Object/ID): The user who created/issued the ticket.
-   `fuel_type` (String, Choices: "PETROL", "DIESEL").
-   `quantity_liters` (Decimal): Amount of fuel in liters.
-   `vehicle_registration_number` (String, Optional): Registration number of the vehicle.
-   `remarks` (String, Optional): Any additional notes.
-   `is_consumed` (Boolean, Default: `false`): `true` if the ticket has been used.
-   `consumed_at` (DateTime, Optional): Timestamp of when the ticket was consumed.
-   `consumed_by_station` (PetrolStation Object/ID, Optional): The station where the ticket was consumed.
-   `driver_name` (String, Optional): Name of the driver.
-   `driver_phone` (String, Optional): Phone number of the driver.
-   `created_at` (DateTime)
-   `updated_at` (DateTime)

([View Model](src/hrm/models/fuel.py:28))

### 3.2. API Endpoints

Base URL: `/api/hrm/fuel-tickets/`

([View API Code](src/hrm/apis/fuel_ticket_apis.py:21))

-   **`GET /api/hrm/fuel-tickets/`**
    -   Description:
        -   For staff users: Lists all fuel tickets.
        -   For non-staff users: Lists fuel tickets dispatched by the current authenticated user.
    -   Permissions: Authenticated users (`IsAuthenticated`).
    -   Response: Array of `FuelTicket` objects (details may vary based on `FuelTicketSerializer`).
        ```json
        [
            {
                "id": 101,
                "ticket_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "dispatched_by": { "id": 5, "username": "manager_user" },
                "fuel_type": "DIESEL",
                "quantity_liters": "50.00",
                "vehicle_registration_number": "XYZ 123",
                "remarks": "Urgent delivery",
                "is_consumed": false,
                "consumed_at": null,
                "consumed_by_station": null,
                "driver_name": "John Doe",
                "driver_phone": "555-1234",
                "created_at": "2024-05-29T08:00:00Z",
                "updated_at": "2024-05-29T08:00:00Z"
            },
            // ... more tickets
        ]
        ```

-   **`POST /api/hrm/fuel-tickets/`**
    -   Description: Creates a new fuel ticket. `dispatched_by` is automatically set to the authenticated user.
    -   Permissions: Authenticated users (`IsAuthenticated`).
    -   Request Body (example based on `FuelTicketSerializer`):
        ```json
        {
            "fuel_type": "PETROL",
            "quantity_liters": "25.50",
            "vehicle_registration_number": "ABC 789",
            "remarks": "For site visit",
            "driver_name": "Jane Smith",
            "driver_phone": "555-5678"
        }
        ```
    -   Response: The created `FuelTicket` object.

-   **`GET /api/hrm/fuel-tickets/{ticket_id}/`**
    -   Description: Retrieves details of a specific fuel ticket. **Note:** The URL parameter here is `{ticket_id}` (the UUID), consistent with custom actions.
    -   Permissions: Authenticated users.
    -   Response: A single `FuelTicket` object.

-   **`PUT /api/hrm/fuel-tickets/{ticket_id}/`**
    -   Description: Updates an existing fuel ticket.
    -   Permissions: Authenticated users (likely restricted to the dispatcher or staff).
    -   Request Body: Fields to update.

-   **`DELETE /api/hrm/fuel-tickets/{ticket_id}/`**
    -   Description: Deletes a fuel ticket.
    -   Permissions: Authenticated users (likely restricted to the dispatcher or staff).

### 3.3. Custom Actions for Fuel Tickets

-   **`POST /api/hrm/fuel-tickets/{ticket_id}/consume/`**
    -   Description: Marks a fuel ticket as consumed. The `{ticket_id}` in the URL is the UUID of the ticket.
    -   Permissions: `AllowAny` (as per API code). Frontend should ensure this action is performed by authorized station personnel or via a secure process.
    -   Request Body (based on `FuelTicketConsumeSerializer` - assuming it requires station ID):
        ```json
        {
            "consumed_by_station_id": 1 // The database ID of the PetrolStation
            // Potentially other fields like actual quantity consumed if different, etc.
            // This depends on the FuelTicketConsumeSerializer definition.
        }
        ```
    -   Success Response (200 OK): The updated `FuelTicket` object (via `FuelTicketSerializer`).
        ```json
        {
            // ... full FuelTicket object with is_consumed = true, consumed_at, consumed_by_station populated ...
        }
        ```
    -   Error Response (400 Bad Request): If the ticket is already consumed.
        ```json
        {
            "error": "Ticket already consumed at [Station Name] on [YYYY-MM-DD HH:MM]."
        }
        ```

-   **`GET /api/hrm/fuel-tickets/{ticket_id}/verify/`**
    -   Description: Verifies the status and details of a fuel ticket using its UUID.
    -   Permissions: `AllowAny`. Useful for public verification by drivers or station staff.
    -   Response (based on `FuelTicketPublicDetailSerializer`): A subset of `FuelTicket` details suitable for public view.
        ```json
        {
            "ticket_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "fuel_type": "DIESEL",
            "quantity_liters": "50.00",
            "vehicle_registration_number": "XYZ 123",
            "is_consumed": true,
            "consumed_at": "2024-05-29T10:30:00Z",
            "consumed_by_station_name": "Main Street Fuel Stop", // Example derived field
            "dispatched_on": "2024-05-29T08:00:00Z" // Example derived field
            // Other fields as defined in FuelTicketPublicDetailSerializer
        }
        ```

### 3.4. Frontend Usage

-   **Creating Tickets:** A form for authorized users to input ticket details (`fuel_type`, `quantity_liters`, `vehicle_registration_number`, `remarks`, `driver_name`, `driver_phone`).
-   **Listing Tickets:** Displaying a table or list of tickets, showing key information like `ticket_id`, `fuel_type`, `quantity_liters`, status (`is_consumed`), and `dispatched_by`. Filters and search functionality would be beneficial.
-   **Viewing a Ticket:** A detail page showing all information for a specific ticket.
-   **Consuming a Ticket:**
    -   An interface for petrol station staff.
    -   Staff enters the `ticket_id` (e.g., from a QR code or manual entry).
    -   Frontend calls `POST /api/hrm/fuel-tickets/{ticket_id}/consume/` with the `consumed_by_station_id` (the ID of their station).
-   **Verifying a Ticket:**
    -   A public-facing page where anyone can enter a `ticket_id`.
    -   Frontend calls `GET /api/hrm/fuel-tickets/{ticket_id}/verify/` to display its status.

## 4. Workflow Examples

### 4.1. Dispatching a Fuel Ticket

1.  **User (e.g., Manager) Logs In:** Authenticates with the system.
2.  **Navigate to Create Ticket:** User accesses the "Create Fuel Ticket" form.
3.  **Fill Form:**
    -   Selects `fuel_type` (Petrol/Diesel).
    -   Enters `quantity_liters`.
    -   Optionally enters `vehicle_registration_number`, `remarks`, `driver_name`, `driver_phone`.
4.  **Submit:** Frontend sends a `POST` request to `/api/hrm/fuel-tickets/` with the form data.
5.  **Confirmation:** System creates the ticket, returns the new ticket object (including its `ticket_id` UUID). The ticket is initially `is_consumed = false`.

### 4.2. Consuming a Fuel Ticket (at Petrol Station)

1.  **Driver Presents Ticket:** Driver provides the `ticket_id` (e.g., on a printout, app, or QR code) at an authorized petrol station.
2.  **Station Staff Accesses System:** Staff uses a dedicated frontend interface for ticket consumption.
3.  **Enter Ticket ID:** Staff inputs the `ticket_id`.
4.  **(Optional) Verify Ticket:** Frontend could first call `GET /api/hrm/fuel-tickets/{ticket_id}/verify/` to show ticket details and confirm it's not already consumed.
5.  **Confirm Consumption:**
    -   Staff confirms the fuel dispensing.
    -   Frontend sends `POST` request to `/api/hrm/fuel-tickets/{ticket_id}/consume/`.
    -   The request body must include `consumed_by_station_id` (the ID of the current petrol station).
6.  **System Update:** API marks the ticket as `is_consumed = true`, records `consumed_at` and `consumed_by_station`.
7.  **Confirmation:** API returns the updated ticket details.

### 4.3. Verifying a Fuel Ticket (Public/Driver)

1.  **Access Verification Page:** User (driver, manager, etc.) navigates to the public ticket verification page.
2.  **Enter Ticket ID:** User inputs the `ticket_id` (UUID).
3.  **Submit:** Frontend sends `GET` request to `/api/hrm/fuel-tickets/{ticket_id}/verify/`.
4.  **Display Status:** Frontend displays the ticket details received from the API, including its consumption status.

## 5. Key API Payloads and Error Handling

### 5.1. Important Serializers (Assumed fields based on models)

-   **`PetrolStationSerializer` (for `GET /api/hrm/petrol-stations/`)**
    -   Includes `id`, `name`, `station_code`, `location_details`, `is_active`, `created_at`, `updated_at`.
-   **`FuelTicketSerializer` (for `GET /api/hrm/fuel-tickets/`, `POST /api/hrm/fuel-tickets/`)**
    -   Includes most fields from the `FuelTicket` model. `dispatched_by` and `consumed_by_station` might be nested objects or IDs.
-   **`FuelTicketConsumeSerializer` (for `POST /api/hrm/fuel-tickets/{ticket_id}/consume/` request body)**
    -   Requires `consumed_by_station_id` (Integer): The database ID of the `PetrolStation`.
-   **`FuelTicketPublicDetailSerializer` (for `GET /api/hrm/fuel-tickets/{ticket_id}/verify/` response)**
    -   A curated set of fields: `ticket_id`, `fuel_type`, `quantity_liters`, `vehicle_registration_number`, `is_consumed`, `consumed_at`, potentially derived fields like `consumed_by_station_name`, `dispatched_on`.

### 5.2. Common HTTP Status Codes & Errors

-   **200 OK:** Successful GET request or successful POST/PUT if data is returned.
-   **201 Created:** Successful POST request that created a new resource.
-   **204 No Content:** Successful DELETE request.
-   **400 Bad Request:**
    -   Invalid request data (e.g., missing required fields, incorrect data types).
    -   Specific error for `consume` action if ticket is already consumed:
        ```json
        { "error": "Ticket already consumed at [Station Name] on [YYYY-MM-DD HH:MM]." }
        ```
-   **401 Unauthorized:** Authentication credentials were not provided or are invalid.
-   **403 Forbidden:** Authenticated user does not have permission to perform the action.
-   **404 Not Found:** The requested resource (e.g., specific ticket or station) does not exist.

Frontend should handle these responses appropriately, displaying user-friendly messages.