# How to Attach Fuel Tickets in Expense Item API

This guide explains how to attach fuel tickets to an `ExpenseItem` using the API, addressing the common "Direct assignment to the forward side of a many-to-many set is prohibited. Use attached_fuel_tickets.set() instead." error.

The `ExpenseItem` serializer has been updated to correctly handle the `attached_fuel_tickets` ManyToMany field. You have two primary ways to attach fuel tickets:

1.  **Using `assigned_fuel_ticket_filters`**: This allows you to dynamically select fuel tickets based on criteria such as IDs, station, or date range. The API will automatically calculate the total bill for these tickets and set the `price_per_item` of the expense item.
2.  **Manually assigning `attached_fuel_tickets` by their IDs**: This allows you to directly specify which fuel tickets (by their primary keys/IDs) should be linked to the expense item. The API will also calculate the total sum of bill amounts for the specified tickets and update the expense item's `price_per_item` accordingly if not explicitly provided.

---

## 1. Attaching Fuel Tickets Using Filters (`assigned_fuel_ticket_filters`)

This method is useful when you want to create an expense item by referencing a set of fuel tickets that match certain criteria. The serializer will query the `FuelTicket` model based on your provided filters, ensure they are consumed, and then associate them with the `ExpenseItem`.

**A. Endpoint:**

`POST /api/statements/expense_items/` (for creating new expense items)
`PATCH /api/statements/expense_items/{id}/` (for updating existing expense items)

**B. Request Body Example (for POST/PATCH):**

```json
{
    "expense": <expense_id>,
    "item_name": "Fuel Expense (Via Filters)",
    "assigned_fuel_ticket_filters": {
        "ids": [1, 5, 10],                        // Optional: List of specific FuelTicket IDs to attach
        "consumed_by_station": 1,                // Optional: Filter by station ID where fuel was consumed
        "consumed_at__range": ["2023-01-01T00:00:00Z", "2023-01-31T23:59:59Z"] // Optional: Date range filter
    },
    "remarks": "Fuel consumed during January 2023 at Station A"
    // Do NOT include "price_per_item" or "quantity" if using filters for price calculation,
    // as these will be automatically calculated based on the attached tickets.
    // If you provide them, they will override the calculated values for the expense item,
    // but the linked tickets' total bill amount will still be computed and available.
}
```

**C. Important Notes:**

*   You can combine `ids` with other filters. If `ids` is provided, only tickets matching those IDs and other specified filters will be considered.
*   Only consumed fuel tickets (`is_consumed=True`) can be attached. The API will validate this.
*   The `item_name`, `quantity` (set to `1.00`), and `price_per_item` for the `ExpenseItem` will be automatically set based on the aggregated `bill_amount` of the selected fuel tickets. You can override `item_name` if needed.

---

## 2. Manually Attaching Fuel Tickets (`attached_fuel_tickets`)

This method allows you to directly pass a list of primary keys (IDs) of `FuelTicket` instances that you want to associate with the `ExpenseItem`. This is suitable when you already know the specific fuel tickets you want to link.

**A. Endpoint:**

`POST /api/statements/expense_items/` (for creating new expense items)
`PATCH /api/statements/expense_items/{id}/` (for updating existing expense items)

**B. Request Body Example (for POST/PATCH):**

```json
{
    "expense": <expense_id>,
    "item_name": "Fuel for Vehicle X",
    "quantity": 1,
    "price_per_item": 5000.00,                      // Optional: If not provided, it will be calculated from attached tickets.
    "attached_fuel_tickets": [2, 4, 7],             // List of FuelTicket IDs (primary keys)
    "remarks": "Fueling up company vehicle X for the week."
}
```

**C. Important Notes:**

*   The `attached_fuel_tickets` field expects a list of `FuelTicket` primary keys (integers).
*   The API will validate that the provided `FuelTicket` instances exist and are marked as `is_consumed=True`.
*   If `price_per_item` and `quantity` are not provided in the request body, they will be automatically calculated based on the sum of `bill_amount` of the `attached_fuel_tickets`. If they are provided, these values will be used for the expense item, but the sum of attached tickets will still be computed internally.
*   When updating an `ExpenseItem`, providing `attached_fuel_tickets` will **completely replace** any previously attached fuel tickets with the new list provided. To retain existing attachments while adding new ones, you would need to fetch the current `attached_fuel_tickets` list first, combine it with new IDs, and then send the complete list in the update request.

---

## Error Handling

If you encounter the error: `{"status": false, "error": "Direct assignment to the forward side of a many-to-many set is prohibited. Use attached_fuel_tickets.set() instead."}`

This error typically occurs when you attempt to directly assign a list of objects or an object to a ManyToManyField during the `create` or `update` operation of a serializer without explicitly handling the `.set()` method. The provided serializer updates properly handle this by popping the `attached_fuel_tickets` from `validated_data` and using `instance.attached_fuel_tickets.set()` after the `ExpenseItem` instance is created or updated.

Ensure you are sending `attached_fuel_tickets` as a list of primary keys (integers), or using the `assigned_fuel_ticket_filters` field as described above. Do not try to send nested objects for `attached_fuel_tickets`.