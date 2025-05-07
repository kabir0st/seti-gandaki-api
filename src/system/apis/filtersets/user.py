from django_filters import DateFromToRangeFilter

from core.utils.viewsets import ExcludeFilterSet
from system.models.user import UserBase


class UserFilterSet(ExcludeFilterSet):
    created_at = DateFromToRangeFilter(field_name='created_at')
    updated_at = DateFromToRangeFilter(field_name='updated_at')

    class Meta:
        model = UserBase
        exclude = ('profile_image', 'groups', 'user_permissions',
                   'is_superuser')
