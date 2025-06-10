from rest_framework.permissions import IsAuthenticated
from core.utils.viewsets import DefaultViewSet

from ..models import Account
from ..serializers import AccountSerializer
from .filtersets.account import AccountFilterSet


class AccountViewSet(DefaultViewSet):
    """
    API endpoint that allows accounts to be viewed or edited.
    """
    queryset = Account.objects.all().order_by('-created_at')
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = AccountFilterSet
    search_fields = ['name', 'account_number', 'bank_name', 'branch_name']
    ordering_fields = ['name', 'account_number', 'bank_name', 'current_amount', 'created_at', 'updated_at']