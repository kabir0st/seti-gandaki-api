# Frontend Guide: Using StatViewSets for Invoice, Purchase, and Expense

This document provides guidance for frontend developers on how to interact with `StatViewSet` endpoints for `Invoice`, `Purchase`, and `Expense` data. It specifically covers how to use the `auto_fill` query parameter to fetch unique values for specific fields, which is useful for populating dropdowns, autocomplete fields, or other UI elements requiring distinct data.

## Introduction to StatViewSets

`StatViewSets` are designed to provide aggregated or distinct data from the backend, optimized for frontend components that require summarized information or lists of unique values. These viewsets can help reduce the amount of data transferred and simplify frontend logic.

## Endpoints

The base URL for the API is assumed to be `/api/v1/`. The specific paths for the stat viewsets will follow a pattern like:

*   **Invoice Stats:** `/api/v1/statements/invoices/stats/`
*   **Purchase Stats:** `/api/v1/statements/purchases/stats/`
*   **Expense Stats:** `/api/v1/statements/expenses/stats/`

*(Note: Please verify the exact endpoint paths from the backend API documentation or by inspecting the available routes.)*

## Using the `auto_fill` Query Parameter

The `auto_fill` query parameter is a powerful feature that allows you to request a list of unique values for a specified field. This is particularly useful for populating UI elements like search filters, dropdown menus, or autocomplete suggestions.

### How it Works

When you include the `auto_fill=<field_name>` query parameter in your GET request to a `StatViewSet` endpoint, the API will return a JSON response containing an array of unique values for the specified `<field_name>`.

### Syntax

`GET /api/v1/statements/<resource>/stats/?auto_fill=<field_name>`

Where:
*   `<resource>` can be `invoices`, `purchases`, or `expenses`.
*   `<field_name>` is the name of the field for which you want to retrieve unique values (e.g., `customer_name`, `supplier_name`, `item_name`, `category_name`).

### Examples

#### 1. Fetching Unique Customer Names from Invoices

To get a list of all unique customer names that appear in invoices:

**Request:**
`GET /api/v1/statements/invoices/stats/?auto_fill=customer_name`

**Expected Response:**
```json
{
  "customer_name": [
    "Customer A",
    "Customer B",
    "Another Client Inc.",
    "John Doe"
  ]
}
```

#### 2. Fetching Unique Supplier Names from Purchases

To get a list of all unique supplier names from purchase bills:

**Request:**
`GET /api/v1/statements/purchases/stats/?auto_fill=supplier_name`

**Expected Response:**
```json
{
  "supplier_name": [
    "Supplier X",
    "Vendor Y Co.",
    "Parts Unlimited Ltd."
  ]
}
```

#### 3. Fetching Unique Expense Category Names

To get a list of all unique category names used in expenses:

**Request:**
`GET /api/v1/statements/expenses/stats/?auto_fill=category_name`

**Expected Response:**
```json
{
  "category_name": [
    "Office Supplies",
    "Travel",
    "Utilities",
    "Software Subscriptions"
  ]
}
```

#### 4. Fetching Unique Item Names (e.g., from Invoice Items or Purchase Items)

If the `StatViewSet` supports querying related item models:

**Request (Example for Invoice Items):**
`GET /api/v1/statements/invoices/stats/?auto_fill=item_name`
*(The exact field name `item_name` might vary based on the backend model structure. It could be `invoiceitem_set__name` or similar if accessing through a related manager.)*

**Expected Response:**
```json
{
  "item_name": [
    "Product Alpha",
    "Service Beta",
    "Component Gamma"
  ]
}
```

### Important Considerations

*   **Field Naming:** The exact `field_name` to use with `auto_fill` depends on the backend model and serializer configuration. Consult the API documentation or the backend team for the correct field names. For related fields (e.g., items within an invoice), the field name might involve double underscores (e.g., `related_model__field_name`).
*   **Performance:** While `auto_fill` is optimized for fetching distinct values, requesting this for very high cardinality fields on extremely large datasets might still have performance implications.
*   **Filtering:** You can often combine `auto_fill` with other filter parameters supported by the `StatViewSet` to get unique values within a specific subset of data. For example:
    `GET /api/v1/statements/invoices/stats/?status=paid&auto_fill=customer_name`
    This would fetch unique customer names only from invoices that have a 'paid' status.

## General Stat Data

Besides `auto_fill`, `StatViewSets` might provide other aggregated data by default or through other query parameters (e.g., total amounts, counts, averages). Refer to the specific API documentation for each `StatViewSet` to understand all available functionalities.

This guide should help frontend developers effectively use the `StatViewSet` endpoints and the `auto_fill` feature to enhance user interfaces with dynamic and relevant data.