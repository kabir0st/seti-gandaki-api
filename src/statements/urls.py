from django.urls import path, include
from rest_framework_nested.routers import DefaultRouter, NestedSimpleRouter
from .apis.purchase_bills import PurchaseBillViewSet, PurchaseItemViewSet
from .apis.business import BusinessViewSet
from .apis.vehicle import VehicleViewSet
from .apis.gatepass import GatePassViewSet
from .apis.triplog import TripLogViewSet

router = DefaultRouter()
router.register('purchase-bills', PurchaseBillViewSet, basename='PurchaseBill')
router.register('businesses', BusinessViewSet, basename='Business')
router.register('vehicles', VehicleViewSet, basename='Vehicle')
router.register('gate-passes', GatePassViewSet, basename='GatePass')
router.register('trip-logs', TripLogViewSet, basename='TripLog')

purchase_bills_router = NestedSimpleRouter(router,
                                           'purchase-bills',
                                           lookup='purchase_bill')
purchase_bills_router.register('purchase-items',
                               PurchaseItemViewSet,
                               basename='purchase-bill-items')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(purchase_bills_router.urls)),
]
