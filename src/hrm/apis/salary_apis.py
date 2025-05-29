from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from hrm.models.salary import SalaryDisbursement
from hrm.serializers import SalaryDisbursementSerializer
from hrm.apis.filtersets.salary import SalaryDisbursementFilter
from core.utils.permissions import IsStaffOrReadOnly # Corrected import


class SalaryDisbursementViewSet(viewsets.ModelViewSet):
    queryset = SalaryDisbursement.objects.select_related('staff', 'created_by').all()
    serializer_class = SalaryDisbursementSerializer
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly] # Corrected permission class
    filterset_class = SalaryDisbursementFilter

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        # Non-staff users can only see salary disbursements they created.
        return self.queryset.filter(created_by=self.request.user)