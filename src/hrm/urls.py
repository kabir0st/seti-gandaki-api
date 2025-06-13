from django.urls import path, include
from rest_framework.routers import DefaultRouter
from hrm.apis.fuel_ticket_apis import PetrolStationViewSet, FuelTicketViewSet, FuelingStatsAPIView # Updated path
from hrm.apis.attendance_apis import AttendanceViewSet # Import AttendanceViewSet
from hrm.apis.salary_apis import SalaryDisbursementViewSet # Import SalaryDisbursementViewSet
from hrm.apis.food_ticket_apis import FoodTicketViewSet # Import FoodTicketViewSet
from hrm.apis.device_management import (
    sync_device_attendance,
    device_logs,
    process_raw_data,
    staff_device_mapping,
    update_staff_device_id
)

router = DefaultRouter()
router.register(r'petrol-stations', PetrolStationViewSet, basename='petrol-station') # Changed basename prefix
router.register(r'fuel-tickets', FuelTicketViewSet, basename='fuel-ticket') # Changed path and basename prefix
router.register(r'attendances', AttendanceViewSet, basename='attendance') # Add attendance route
router.register(r'salary-disbursements', SalaryDisbursementViewSet, basename='salary-disbursement') # Add salary disbursement route
router.register(r'food-tickets', FoodTicketViewSet, basename='food-ticket') # Add food ticket route


urlpatterns = [
    path('', include(router.urls)),
    path('fueling-stats/', FuelingStatsAPIView.as_view(), name='fueling-stats'),
    
    # ZKTeco Device Management APIs
    path('device/sync/', sync_device_attendance, name='sync-device-attendance'),
    path('device/logs/', device_logs, name='device-logs'),
    path('device/process-raw/', process_raw_data, name='process-raw-data'),
    path('device/staff-mapping/', staff_device_mapping, name='staff-device-mapping'),
    path('device/update-staff-device/', update_staff_device_id, name='update-staff-device-id'),
]
