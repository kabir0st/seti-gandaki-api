import json
from decimal import Decimal

from django.core.cache import cache
from django.db.models import (CharField, FileField, ImageField, JSONField,
                              TextField, Value)
from django.db.models.functions import Concat
from django_filters import (CharFilter, DateTimeFromToRangeFilter, FilterSet)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter

from core.utils.functions import (get_all_exportable_fields, get_or_set_cache,
                                  get_unique_queryset)

EXCLUDE = [ImageField, FileField, TextField, JSONField]
EXCLUDE_FIELD_NAMES = ['password', 'is_superuser']


class ExcludeFilterSet(FilterSet):
    exclude = CharFilter(method='filter_exclude', label='Exclude')

    def filter_exclude(self, queryset, name, value):
        try:
            exclude_ids = [int(i) for i in value.split(',')]
            return queryset.exclude(id__in=exclude_ids)
        except ValueError:
            return queryset


class DefaultFilterSet(ExcludeFilterSet):
    created_at = DateTimeFromToRangeFilter(field_name='created_at')
    updated_at = DateTimeFromToRangeFilter(field_name='updated_at')
    search = CharFilter(method='filter_search', label='Search')

    def filter_search(self, queryset, name, value):
        view = self.request.parser_context.get("view", None)
        filter_backend = SearchFilter()
        queryset = filter_backend.filter_queryset(self.request, queryset, view)
        return queryset


class UserIncludedFilterSet(ExcludeFilterSet):
    user__name = CharFilter(method='filter_by_name', label='User Name')
    user__email = CharFilter(field_name='user__email', lookup_expr='icontains')

    def filter_by_name(self, queryset, name, value):
        return queryset.annotate(
            full_name=Concat('user__family_name',
                             Value(' '),
                             'user__given_name',
                             output_field=CharField())).filter(
                                 full_name__icontains=value)


def find_decimal_fields(nested_dict, path=None):
    if path is None:
        path = []

    decimal_fields = []

    for key, value in nested_dict.items():
        current_path = path + [key]
        if isinstance(value, dict):
            decimal_fields.extend(find_decimal_fields(value, current_path))
        elif isinstance(value, Decimal):
            decimal_fields.append(".".join(current_path))

    return decimal_fields


class DefaultViewSet(ModelViewSet):

    @property
    def ordering_fields(self):
        try:
            queryset = self.queryset or self.get_queryset()
            return [
                field.name for field in queryset.model._meta.fields if not any(
                    isinstance(field, e)
                    for e in EXCLUDE) and field.name not in EXCLUDE_FIELD_NAMES
            ]
        except AttributeError:
            return []

    @property
    def filterset_fields(self):
        try:
            queryset = self.queryset or self.get_queryset()
            return [
                field.name for field in queryset.model._meta.fields if not any(
                    isinstance(field, e)
                    for e in EXCLUDE) and field.name not in EXCLUDE_FIELD_NAMES
            ]
        except AttributeError:
            return []

    # @action(methods=['GET'], detail=False)
    # def export(self, request, *args, **kwargs):
    #     start = int(request.GET.get('start', 0))
    #     end = int(
    #         request.GET['end']
    #     ) if 'end' in request.GET and request.GET['end'] != 'None' else None

    #     exclude = request.GET.get('exclude', [])
    #     if exclude:
    #         exclude = exclude.split(',')
    #     include_relations = request.GET.get('include_relations', [])
    #     if include_relations:
    #         include_relations = include_relations.split(',')
    #     try:
    #         queryset = self.apply_filters(request)
    #     except Exception as e:
    #         raise APIException('There is a problem applying filters.') from e
    #     document_name = request.GET.get('document_name',
    #                                     queryset.model.__name__)
    #     if document_name:
    #         document_name = str(document_name).title()
    #     model = f'{queryset.model._meta.app_label}.{queryset.model.__name__}'
    #     response = {
    #         'status':
    #         True,
    #         'document':
    #         export_data(model, [item.id for item in queryset[start:end]],
    #                     exclude, include_relations, document_name)
    #     }
    #     return Response(response)

    def filter_by_unique(self, queryset):
        return get_unique_queryset(queryset)

    def list(self, request, *args, **kwargs):
        model_name = self.queryset.model.__name__.lower()
        # for caching purposes
        params = request.query_params.dict()
        cache_for_params = getattr(self, 'cache_for_params',
                                   [{
                                       'page': '1',
                                       'size': '20',
                                       'id_pk': self.kwargs.get('id_pk', None)
                                   }])
        cache_key = None
        # check for cache
        response = None
        if params in cache_for_params:
            cached_data, cache_key = get_or_set_cache(model_name, params)
            if cached_data:
                response = Response(json.loads(cached_data))
                response['data-type'] = 'cached'
        if not response:
            response = super().list(request, *args, **kwargs)
            response['data-type'] = 'fresh'
            if cache_key:
                cache.set(cache_key, json.dumps(response.data), 30)
        response['Export-Fields'] = get_all_exportable_fields(
            self.queryset.first() if self.queryset.first() else None)
        return response


class SingletonViewSet(ModelViewSet):

    def destroy(self, request, *args, **kwargs):
        return Response({'status': False, 'msg': 'Cannot remove settings.'})

    def retrieve_instance(self):
        instance = self.get_queryset().first()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def list(self, request):
        return self.retrieve_instance()

    def retrieve(self, request, *args, **kwargs):
        return self.retrieve_instance()

    def create(self, request, *args, **kwargs):
        obj = self.get_queryset().first()
        if obj is None:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        else:
            serializer = self.get_serializer(instance=obj, data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED,
                        headers=headers)
