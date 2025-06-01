# Gate Pass Filters

This document outlines the available filters for the Gate Pass API endpoint.

## Filtering by Creation Date

You can filter gate passes based on their creation date using the `created_at_after` and `created_at_before` query parameters. These parameters accept datetime strings in ISO 8601 format (e.g., `YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DD`).

### `created_at_after`

To retrieve gate passes created on or after a specific date and time.

**Example:**

To get all gate passes created on or after January 1st, 2024, at midnight UTC:

```
/api/statements/gate-passes/?created_at_after=2024-01-01T00:00:00Z
```

Or, for just the date (time will default to 00:00:00):
```
/api/statements/gate-passes/?created_at_after=2024-01-01
```

### `created_at_before`

To retrieve gate passes created on or before a specific date and time.

**Example:**

To get all gate passes created on or before December 31st, 2024, at 23:59:59 UTC:

```
/api/statements/gate-passes/?created_at_before=2024-12-31T23:59:59Z
```

Or, for just the date (time will default to 00:00:00 of that day, so effectively it means *before* the start of the specified day if only date is provided. To include the entire day, you'd typically use the next day as `created_at_before` or specify the time as `23:59:59`):
```
/api/statements/gate-passes/?created_at_before=2024-12-31
```

### Combining `created_at_after` and `created_at_before`

You can use both parameters together to specify a date range.

**Example:**

To get all gate passes created during the month of November 2024:

```
/api/statements/gate-passes/?created_at_after=2024-11-01&created_at_before=2024-11-30T23:59:59Z
```

## Other Available Filters

The Gate Pass API also supports other filters such as:

*   `vehicle_license_plate`: Exact match for vehicle's license plate.
*   `vehicle_license_plate__icontains`: Case-insensitive containment match for vehicle's license plate.
*   `license_plate`: Exact match for license plate (if vehicle not specified).
*   `license_plate__icontains`: Case-insensitive containment match for license plate.
*   `driver_name__icontains`: Case-insensitive containment match for driver's name.
*   `driver_phone`: Exact match for driver's phone number.
*   `entry_time_after`: Gate passes with entry time on or after the specified datetime.
*   `entry_time_before`: Gate passes with entry time on or before the specified datetime.
*   `exit_time_after`: Gate passes with exit time on or after the specified datetime.
*   `exit_time_before`: Gate passes with exit time on or before the specified datetime.
*   `is_open`: Boolean filter (`true` or `false`) to find gate passes that are still open (no exit time recorded).

Refer to the API documentation or swagger for a complete list and detailed usage.