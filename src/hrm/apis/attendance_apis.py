from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from hrm.models.attendance import Attendance
from hrm.serializers import AttendanceSerializer
from core.utils.permissions import IsStaffOrReadOnly # Changed IsAdminOrReadOnly to IsStaffOrReadOnly
from core.utils.viewsets import DefaultViewSet # Changed TimeStampedViewSetMixin to DefaultViewSet

class AttendanceViewSet(DefaultViewSet): # Removed TimeStampedViewSetMixin, inheriting from DefaultViewSet
    """
    API endpoint that allows attendances to be viewed or edited.
    """
    queryset = Attendance.objects.select_related('staff').all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly] # Changed IsAdminOrReadOnly to IsStaffOrReadOnly
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'staff__id': ['exact'],
        'staff__name': ['icontains'],
        'date': ['exact', 'gte', 'lte', 'range'],
        'status': ['exact', 'in'],
    }
    search_fields = ['staff__name', 'remarks']
    ordering_fields = ['date', 'staff__name', 'status', 'created_at']
    ordering = ['-date', 'staff__name']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Add any specific filtering for the user if needed, e.g.,
        # if not self.request.user.is_staff:
        #     queryset = queryset.filter(staff__user=self.request.user) # Assuming staff is linked to user
        return queryset

    # perform_create and perform_update are usually handled by DefaultViewSet or ModelViewSet
    # If specific logic is needed before or after save, uncomment and implement.
    # def perform_create(self, serializer):
    #     # Example: serializer.save(created_by=self.request.user)
    #     super().perform_create(serializer)

    # def perform_update(self, serializer):
    #     # Example: serializer.save(updated_by=self.request.user)
    #     super().perform_update(serializer)