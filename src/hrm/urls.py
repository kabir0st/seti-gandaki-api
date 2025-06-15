from django.urls import path, include
from rest_framework.routers import DefaultRouter
from hrm.apis.fuel_ticket_apis import PetrolStationViewSet, FuelTicketViewSet, FuelingStatsAPIView # Updated path
from hrm.apis.attendance_apis import AttendanceViewSet # Import AttendanceViewSet
from hrm.apis.salary_apis import SalaryDisbursementViewSet # Import SalaryDisbursementViewSet
from hrm.apis.food_ticket_apis import FoodTicketViewSet # Import FoodTicketViewSet


router = DefaultRouter()
router.register(r'petrol-stations', PetrolStationViewSet, basename='petrol-station')
router.register(r'fuel-tickets', FuelTicketViewSet, basename='fuel-ticket') # Changed path and basename prefix
router.register(r'attendances', AttendanceViewSet, basename='attendance') # Add attendance route
router.register(r'salary-disbursements', SalaryDisbursementViewSet, basename='salary-disbursement') # Add salary disbursement route
router.register(r'food-tickets', FoodTicketViewSet, basename='food-ticket') # Add food ticket route


urlpatterns = [
    path('', include(router.urls)),
    path('fueling-stats/', FuelingStatsAPIView.as_view(), name='fueling-stats'),
]
