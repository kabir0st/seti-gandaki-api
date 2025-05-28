from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = BusinessFilterSet
    search_fields = ['name', 'registration_number']
