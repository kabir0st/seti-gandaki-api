from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from core.utils.viewsets import DefaultViewSet

from ..models import Business
from ..serializers import BusinessSerializer
from .filtersets.business import BusinessFilterSet


class BusinessViewSet(DefaultViewSet):
    """
    API endpoint that allows businesses to be viewed or edited.
    """
    queryset = Business.objects.all().order_by('-created_at')
    serializer_class = BusinessSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = BusinessFilterSet
    search_fields = ['name', 'registration_number']

    @action(detail=True, methods=['post'], url_path='reconcile')
    def reconcile_business(self, request, pk=None):
        """
        Reconcile business balance based on all related payments
        """
        business = self.get_object()
        
        try:
            result = business.reconcile_from_payments()
            serializer = self.get_serializer(business)
            return Response({
                'detail': 'Business reconciliation completed.',
                'reconciliation_result': result,
                'business': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'detail': f'Reconciliation failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='reconcile-all')
    def reconcile_all_businesses(self, request):
        """
        Reconcile all businesses based on their related payments
        """
        try:
            results = []
            businesses = Business.objects.all()
            
            for business in businesses:
                result = business.reconcile_from_payments()
                results.append({
                    'business_id': business.id,
                    'business_name': business.name,
                    'reconciliation_result': result
                })
            
            return Response({
                'detail': f'Reconciled {len(businesses)} businesses.',
                'results': results
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'detail': f'Bulk reconciliation failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
