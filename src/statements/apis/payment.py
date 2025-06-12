from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from core.utils.viewsets import DefaultViewSet
from statements.models.payments import Payment
from statements.serializers import PaymentSerializer
from statements.apis.filtersets.payment import PaymentFilterSet
from django.db.models import Sum

class PaymentViewSet(DefaultViewSet):
    """
    API endpoint that allows payments to be viewed or edited.
    """
    queryset = Payment.objects.all().select_related('invoice', 'purchase_bill', 'expense', 'created_by').order_by('-created_at')
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = PaymentFilterSet
    search_fields = [
        'invoice__invoice_number',
        'purchase_bill__purchase_bill_number',
        'expense__bill_number', # Assuming Expense has a bill_number
        'remarks',
        'created_by__username', # Assuming UserBase has a username
    ]
    ordering_fields = ['amount', 'created_at', 'updated_at', 'header']

    @action(detail=True, methods=['post'], url_path='refund')
    def refund_payment(self, request, pk=None):
        """
        Refunds a payment and reverts its effects.
        """
        payment = self.get_object()
        
        try:
            payment.refund()
            serializer = self.get_serializer(payment)
            return Response({
                'detail': 'Payment refunded successfully.',
                'payment': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # Exclude refunded payments
        queryset = queryset.filter(is_refunded=False)
        stats = queryset.values('header', 'action').annotate(
            total_amount=Sum('amount')
        ).order_by('header', 'action')
        # Format stats into the desired structure
        formatted_stats = {}
        for stat in stats:
            header = stat['header']
            action = stat['action']
            amount = stat['total_amount'] or 0
            if header not in formatted_stats:
                formatted_stats[header] = {}
            formatted_stats[header][action] = float(amount)
        response_properties = {
            'payment_stats': formatted_stats
        }
        response = super().list(request, *args, **kwargs)
        response['response-properties'] = response_properties
        return response

    def update(self, request, *args, **kwargs):
        """
        Prevent updates to existing payments - they can only be refunded
        """
        return Response({
            'detail': 'Payments cannot be modified once created. Use the refund endpoint to refund a payment.'
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        """
        Prevent partial updates to existing payments - they can only be refunded
        """
        return Response({
            'detail': 'Payments cannot be modified once created. Use the refund endpoint to refund a payment.'
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=['get'], url_path='validate-balance-impact')
    def validate_balance_impact(self, request, pk=None):
        """
        Validate the balance impact of a payment without applying it
        """
        from statements.models.payments import get_payment_balance_impact
        
        payment = self.get_object()
        
        try:
            impact = get_payment_balance_impact(payment)
            return Response({
                'payment_id': payment.id,
                'payment_amount': payment.amount,
                'payment_action': payment.action,
                'payment_header': payment.header,
                'business_impact': impact['business_impact'],
                'account_impact': impact['account_impact'],
                'related_business': payment.related_business.name if payment.related_business else None,
                'related_account': payment.related_account.name if payment.related_account else None,
                'has_statements': bool(payment.invoice or payment.purchase_bill or payment.expense),
                'statement_type': (
                    'invoice' if payment.invoice else
                    'purchase_bill' if payment.purchase_bill else
                    'expense' if payment.expense else
                    'none'
                )
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'detail': f'Validation failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='reconcile-all')
    def reconcile_all_payments(self, request):
        """
        Reconcile all accounts and businesses based on payments
        """
        try:
            from statements.models.payments import Account
            from statements.models.business import Business
            
            account_results = []
            business_results = []
            
            # Reconcile all accounts
            for account in Account.objects.all():
                result = account.reconcile_from_payments()
                account_results.append({
                    'account_id': account.id,
                    'account_name': account.name,
                    'reconciliation_result': result
                })
            
            # Reconcile all businesses
            for business in Business.objects.all():
                result = business.reconcile_from_payments()
                business_results.append({
                    'business_id': business.id,
                    'business_name': business.name,
                    'reconciliation_result': result
                })
            
            return Response({
                'detail': f'Reconciled {len(Account.objects.all())} accounts and {len(Business.objects.all())} businesses.',
                'account_results': account_results,
                'business_results': business_results
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'detail': f'Bulk reconciliation failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)