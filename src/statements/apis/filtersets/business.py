import django_filters
from ...models.business import Business


class BusinessFilterSet(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    registration_number = django_filters.CharFilter(lookup_expr='iexact')
    contact_person = django_filters.CharFilter(lookup_expr='icontains')
    contact_email = django_filters.CharFilter(lookup_expr='iexact')
    phone_number = django_filters.CharFilter(lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()
    is_customer = django_filters.BooleanFilter()
    is_vendor = django_filters.BooleanFilter()

    class Meta:
        model = Business
        fields = [
            'name',
            'registration_number',
            'contact_person',
            'contact_email',
            'phone_number',
            'is_active',
            'is_customer',
            'is_vendor',
        ]
