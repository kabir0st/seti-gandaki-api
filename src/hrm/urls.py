from django.urls import path, include
from rest_framework.routers import DefaultRouter
from hrm.apis.fuel_ticket_apis import PetrolStationViewSet, FuelTicketViewSet # Updated path

router = DefaultRouter()
router.register(r'petrol-stations', PetrolStationViewSet, basename='petrol-station') # Changed basename prefix
router.register(r'fuel-tickets', FuelTicketViewSet, basename='fuel-ticket') # Changed path and basename prefix


urlpatterns = [
    path('', include(router.urls)),
]