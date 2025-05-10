from rest_framework import permissions

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
    permission_classes = [permissions.IsAuthenticated
                          ]  # Adjust permissions as needed
    filterset_class = BusinessFilterSet
    search_fields = [
        'name', 'registration_number', 'contact_person', 'contact_email',
        'phone_number'
    ]
    ordering_fields = [
        'name', 'registration_number', 'created_at', 'updated_at'
    ]
