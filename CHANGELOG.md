# Changelog

## Latest Commit: 3459588 - Kabir S. Tamari, 2025-05-28 : added invoice and invoice item with system settings

### Summary of Changes:
This commit introduces a new invoicing system with the following key changes:

- **New Models:** `Invoice` and `InvoiceItem` have been added to manage invoicing functionalities.
- **New API Endpoints:**
    - `GET /invoices/`: Retrieve a list of all invoices.
    - `POST /invoices/`: Create a new invoice.
    - `GET /invoices/{id}/`: Retrieve details of a specific invoice.
    - `PUT /invoices/{id}/`: Update a specific invoice.
    - `PATCH /invoices/{id}/`: Partially update a specific invoice.
    - `DELETE /invoices/{id}/`: Delete a specific invoice.
    - `GET /invoices/{invoice_pk}/items/`: Retrieve a list of invoice items for a specific invoice.
    - `POST /invoices/{invoice_pk}/items/`: Create a new invoice item for a specific invoice.
    - `GET /invoices/{invoice_pk}/items/{id}/`: Retrieve details of a specific invoice item.
    - `PUT /invoices/{invoice_pk}/items/{id}/`: Update a specific invoice item.
    - `PATCH /invoices/{invoice_pk}/items/{id}/`: Partially update a specific invoice item.
    - `DELETE /invoices/{invoice_pk}/items/{id}/`: Delete a specific invoice item.

### Frontend Implementation/Changes Required:
Frontend applications will need to:
- **Integrate with New Invoice APIs:** Implement logic to interact with the new `/invoices/` and `/invoices/{invoice_pk}/items/` endpoints for managing invoices and their respective items.
- **Update Data Models:** Adjust frontend data models to align with the new `InvoiceSerializer` and `InvoiceItemSerializer` structures. Key fields include:
    - **Invoice:** `customer`, `customer_name`, `customer_phone_number`, `customer_pan`, `invoiced_on`, `due_on`, `invoice_number`, `status`, `delivery_charge`, `delivery_location`, `delivery_note`, `tracking_code`, `weight_unit`, `total_weight`, `additional_charge_amount`, `additional_charge_note`, `additional_discount_amount`, `additional_discount_note`, `sub_total_amount`, `total_discount_amount`, `total_taxable_amount`, `total_tax_amount`, `bill_amount`, `paid_amount`, `serial`, `fiscal_year_ad`, `fiscal_year_bs`, `is_paid`, `remarks`, `is_taxable`, `invoice_items`.
    - **InvoiceItem:** `item_name`, `quantity`, `unit`, `price_per_item`, `discount_percent`, `discount_remarks`, `sub_total_amount`, `bill_amount`, `tax_percent`, `taxable_amount`, `tax_amount`, `vat_applicable`, `is_marked_as_complete`, `profit_flow`.
- **UI/UX Development:** Develop new UI components for creating, viewing, editing, and managing invoices and their items. This includes forms for data entry, tables for displaying lists, and detailed views for individual invoices.
- **Validation Logic:** Implement frontend validation based on the serializer's read-only fields and other constraints (e.g., `is_taxable` cannot be changed if invoice is not in draft and has an invoice number).
- **State Management:** Incorporate the new invoice data into the application's state management system.
- **Routing:** Add new routes for the invoice management sections.
- **Error Handling:** Implement robust error handling for API interactions.
- **User Permissions:** Ensure proper handling of user permissions for accessing invoice functionalities.
- **Number Generation:** Note that `invoice_number`, `fiscal_year_ad`, `fiscal_year_bs`, `serial`, `sub_total_amount`, `total_discount_amount`, `total_taxable_amount`, `total_tax_amount`, `bill_amount`, `paid_amount`, and `is_paid` are read-only fields and are generated/calculated on the backend.
- **`is_taxable` field:** This field is now part of the `Invoice` model and affects invoice number generation. Frontend should consider this when creating new invoices.

## Latest Commit: b91f76e - Kabir S. Tamari, 3 days ago : serializer updated

### Changes:
```diff
--- a/src/statements/serializers.py
+++ b/src/statements/serializers.py
@@ -71,7 +71,7 @@ class GatePassSerializer(serializers.ModelSerializer):
 
 class TripLogSerializer(serializers.ModelSerializer):
 -    gate_pass_details = VehicleSerializer(source='gate_pass', read_only=True)
-+    gate_pass_details = GatePassSerializer(source='gate_pass', read_only=True)
+    gate_pass_details = GatePassSerializer(source='gate_pass', read_only=True)
 
      class Meta:
          model = TripLog
```

## Previous Commit: 17f96ff - Kabir S. Tamari, 4 days ago : fixed

(No diff available for this commit as the diff was generated between the last two commits.)