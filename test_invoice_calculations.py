#!/usr/bin/env python
"""
Test script to verify InvoiceItem bill amount calculations with decimal quantities
"""
import os
import sys
import django
from decimal import Decimal

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from statements.models.invoice.invoice import Invoice, InvoiceStatus
from statements.models.invoice.invoice_item import InvoiceItem
from statements.models.business import Business
from statements.models.settings import StatementSettings


def test_invoice_item_calculations():
    """Test invoice item calculations with decimal quantities"""
    print("Testing InvoiceItem calculations with decimal quantities...")
    print("===========================================")
    bus, _ = Business.objects.get_or_create(name="Default")
    StatementSettings.objects.get_or_create(default_quick_invoice_business=bus)

    # Create a test business
    business, created = Business.objects.get_or_create(name="Test Business",
                                                       defaults={
                                                           'phone_number':
                                                           '1234567890',
                                                           'address':
                                                           'Test Address',
                                                           'current_amount':
                                                           Decimal('0.00')
                                                       })

    # Create a test invoice
    invoice = Invoice.objects.create(customer=business,
                                     status=InvoiceStatus.DRAFT,
                                     is_taxable=False)

    print(f"Created test invoice: {invoice}")

    # Test case 1: Basic calculation with decimal quantity
    print("\nTest Case 1: Basic calculation with decimal quantity")
    item1 = InvoiceItem.objects.create(
        invoice=invoice,
        item_name="Test Item 1",
        quantity=Decimal('2.5'),  # Decimal quantity
        price_per_item=Decimal('100.00'),
        discount_percent=Decimal('10.00'))

    print(
        f"Item 1 - Quantity: {item1.quantity}, Price: {item1.price_per_item}")
    print("Expected sub_total: 2.5 * 100.00 = 250.00")
    print(f"Actual sub_total: {item1.sub_total_amount}")
    print("Expected discount: 250.00 * 10% = 25.00")
    print(f"Actual discount: {item1.discount_amount}")
    print("Expected bill_amount: 250.00 - 25.00 = 225.00")
    print(f"Actual bill_amount: {item1.bill_amount}")

    # Test case 2: Small decimal quantity
    print("\nTest Case 2: Small decimal quantity")
    item2 = InvoiceItem.objects.create(
        invoice=invoice,
        item_name="Test Item 2",
        quantity=Decimal('0.75'),  # Small decimal quantity
        price_per_item=Decimal('200.00'),
        discount_percent=Decimal('5.00'))

    print(
        f"Item 2 - Quantity: {item2.quantity}, Price: {item2.price_per_item}")
    print("Expected sub_total: 0.75 * 200.00 = 150.00")
    print(f"Actual sub_total: {item2.sub_total_amount}")
    print("Expected discount: 150.00 * 5% = 7.50")
    print(f"Actual discount: {item2.discount_amount}")
    print("Expected bill_amount: 150.00 - 7.50 = 142.50")
    print(f"Actual bill_amount: {item2.bill_amount}")

    # Test case 3: Update quantity and verify recalculation
    print("\nTest Case 3: Update quantity and verify recalculation")
    item1.quantity = Decimal('3.25')
    item1.save()

    print(
        f"Updated Item 1 - Quantity: {item1.quantity}, Price: {item1.price_per_item}"
    )
    print("Expected sub_total: 3.25 * 100.00 = 325.00")
    print(f"Actual sub_total: {item1.sub_total_amount}")
    print("Expected discount: 325.00 * 10% = 32.50")
    print(f"Actual discount: {item1.discount_amount}")
    print("Expected bill_amount: 325.00 - 32.50 = 292.50")
    print(f"Actual bill_amount: {item1.bill_amount}")

    # Test case 4: Verify invoice totals
    print("\nTest Case 4: Verify invoice totals")
    invoice.refresh_from_db()
    print(f"Invoice sub_total_amount: {invoice.sub_total_amount}")
    print(f"Invoice total_discount_amount: {invoice.total_discount_amount}")
    print(f"Invoice bill_amount: {invoice.bill_amount}")

    expected_sub_total = Decimal('475.00')  # 325.00 + 150.00
    expected_total_discount = Decimal('40.00')  # 32.50 + 7.50
    expected_bill_amount = Decimal('435.00')  # 475.00 - 40.00

    print(f"Expected sub_total: {expected_sub_total}")
    print(f"Expected total_discount: {expected_total_discount}")
    print(f"Expected bill_amount: {expected_bill_amount}")

    # Test case 5: Delete item and verify recalculation
    print("\nTest Case 5: Delete item and verify recalculation")
    item2.delete()
    invoice.refresh_from_db()

    print("After deleting Item 2:")
    print(f"Invoice sub_total_amount: {invoice.sub_total_amount}")
    print(f"Invoice total_discount_amount: {invoice.total_discount_amount}")
    print(f"Invoice bill_amount: {invoice.bill_amount}")

    expected_sub_total_after_delete = Decimal('325.00')
    expected_total_discount_after_delete = Decimal('32.50')
    expected_bill_amount_after_delete = Decimal('292.50')

    print(f"Expected sub_total: {expected_sub_total_after_delete}")
    print(f"Expected total_discount: {expected_total_discount_after_delete}")
    print(f"Expected bill_amount: {expected_bill_amount_after_delete}")

    # Cleanup
    invoice.delete()
    if created:
        business.delete()

    print("\nTest completed successfully!")


if __name__ == '__main__':
    test_invoice_item_calculations()
