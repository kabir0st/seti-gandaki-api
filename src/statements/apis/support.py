from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from core.utils.viewsets import DefaultViewSet
from ..serializers import StaffSerializer
from ..models.support import Staff
from .filtersets import StaffFilterSet


class StaffViewSet(DefaultViewSet):
    queryset = Staff.objects.all().order_by('-updated_at')
    serializer_class = StaffSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = StaffFilterSet
    search_fields = [
        'name',
        'phone_number',
        'pan',
    ]
