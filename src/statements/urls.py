from .apis.cashcounter_apis import CashCounterViewSet
from django.urls import path, include
from .apis.purchase_bills import PurchaseBillViewSet, PurchaseItemViewSet, PurchasedItemStatViewSet
from .apis.business import BusinessViewSet
from .apis.vehicle import VehicleViewSet
from .apis.gatepass import GatePassViewSet
from .apis.triplog import TripLogViewSet
from .apis.support import StaffViewSet
from .apis.invoice import InvoiceViewSet, InvoiceItemViewSet # Keep this for existing views
from .apis.invoice_items import InvoicedItemStatViewSet # New import for stats
from .apis.settings import StatementSettingsAPIView
from .apis.expense import ExpenseCategoryViewSet, ExpenseViewSet, ExpenseItemViewSet # Keep this
from .apis.expense_items import ExpensedItemStatViewSet # New import for expense stats
from .apis.payment import PaymentViewSet # Added import
from rest_framework_nested.routers import SimpleRouter, NestedSimpleRouter
from statements.apis.statistics import StatementStatisticsView


router = SimpleRouter()
router.register('businesses', BusinessViewSet, basename='Business')
router.register('vehicles', VehicleViewSet, basename='Vehicle')
router.register('gate-passes', GatePassViewSet, basename='GatePass')
router.register('trip-logs', TripLogViewSet, basename='TripLog')
router.register('staffs', StaffViewSet, basename='Staff')
router.register('expense-categories', ExpenseCategoryViewSet, basename='ExpenseCategory')

router.register('purchase-bills', PurchaseBillViewSet, basename='PurchaseBill')

router.register('invoices', InvoiceViewSet, basename='Invoice')

router.register('expenses', ExpenseViewSet, basename='Expense')
router.register('payments', PaymentViewSet, basename='Payment')
router.register('purchase-item-stats', PurchasedItemStatViewSet, basename='PurchasedItemStat')
router.register('invoiced-item-stats', InvoicedItemStatViewSet, basename='InvoicedItemStat')
router.register('expensed-item-stats', ExpensedItemStatViewSet, basename='ExpensedItemStat')
router.register('cash-counters', CashCounterViewSet, basename='CashCounter')

purchase_bills_router = NestedSimpleRouter(router,
                                           'purchase-bills',
                                           lookup='purchase_bill')

purchase_bills_router.register('items',
                               PurchaseItemViewSet,
                               basename='purchase-bill-items')

invoices_router = NestedSimpleRouter(router, 'invoices', lookup='invoice')
invoices_router.register('items', InvoiceItemViewSet, basename='invoice-items')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(purchase_bills_router.urls)),
    path('', include(invoices_router.urls)),
]

expenses_router = NestedSimpleRouter(router, 'expenses', lookup='expense')
expenses_router.register('items', ExpenseItemViewSet, basename='expense-items')

urlpatterns += [
    path('', include(expenses_router.urls)),
    path('settings/', StatementSettingsAPIView.as_view(), name='statement-settings'),
    path('statistics/', StatementStatisticsView.as_view(), name='statement-statistics'),
]
