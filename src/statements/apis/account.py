from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
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

    @action(detail=True, methods=['post'], url_path='reconcile')
    def reconcile_account(self, request, pk=None):
        """
        Reconcile account balance based on all related payments
        """
        account = self.get_object()
        
        try:
            result = account.reconcile_from_payments()
            serializer = self.get_serializer(account)
            return Response({
                'detail': 'Account reconciliation completed.',
                'reconciliation_result': result,
                'account': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'detail': f'Reconciliation failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='reconcile-all')
    def reconcile_all_accounts(self, request):
        """
        Reconcile all accounts based on their related payments
        """
        try:
            results = []
            accounts = Account.objects.all()
            
            for account in accounts:
                result = account.reconcile_from_payments()
                results.append({
                    'account_id': account.id,
                    'account_name': account.name,
                    'reconciliation_result': result
                })
            
            return Response({
                'detail': f'Reconciled {len(accounts)} accounts.',
                'results': results
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'detail': f'Bulk reconciliation failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)