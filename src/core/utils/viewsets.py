import json
from decimal import Decimal
from datetime import datetime

from django.core.cache import cache
from django.db.models import (CharField, FileField, ImageField, JSONField,
                              TextField, Value)
from django.db.models.functions import Concat
from django.http import HttpResponse
from django_filters import (CharFilter, DateTimeFromToRangeFilter, FilterSet)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter
from rest_framework.exceptions import APIException

from core.utils.functions import (export_data, export_data_from_response, get_all_exportable_fields, get_or_set_cache,
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
    search_fields = CharFilter(method='filter_search', label='Search')

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

    @action(methods=['GET'], detail=False)
    def export(self, request, *args, **kwargs):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Get export configuration from request parameters
        human_readable_headers = request.GET.get('human_readable_headers', 'true').lower() == 'true'
        auto_exclude_non_human_fields = request.GET.get('auto_exclude_non_human_fields', 'true').lower() == 'true'
        
        # Check if this is a view with custom logic (no direct model queryset)
        # or if the view has a custom export_data method
        if hasattr(self, 'export_data') and callable(getattr(self, 'export_data')):
            # Use custom export_data method from the view
            try:
                data = self.export_data(request, *args, **kwargs)
                view_name = self.__class__.__name__.replace('ViewSet', '').replace('View', '')
                
                # Generate document name
                custom_name = request.GET.get('document_name', '')
                if custom_name:
                    document_name = f"{custom_name}_{timestamp}"
                else:
                    document_name = f"{view_name}_export_{timestamp}"
                
                # Export from response data
                excel_file = export_data_from_response(data, document_name, human_readable_headers)
                
            except Exception as e:
                raise APIException(f'Error in custom export: {str(e)}') from e
                
        else:
            # Standard model-based export
            start = int(request.GET.get('start', 0))
            end = int(
                request.GET['end']
            ) if 'end' in request.GET and request.GET['end'] != 'None' else None

            exclude = request.GET.get('exclude', [])
            if exclude:
                exclude = exclude.split(',')
            include_relations = request.GET.get('include_relations', [])
            if include_relations:
                include_relations = include_relations.split(',')
            
            try:
                # Try to get data from list() method for views with custom logic
                if not hasattr(self, 'queryset') or self.queryset is None:
                    # This view doesn't have a direct queryset, use list() method
                    list_response = self.list(request, *args, **kwargs)
                    if hasattr(list_response, 'data'):
                        data = list_response.data
                        view_name = self.__class__.__name__.replace('ViewSet', '').replace('View', '')
                        
                        # Generate document name
                        custom_name = request.GET.get('document_name', '')
                        if custom_name:
                            document_name = f"{custom_name}_{timestamp}"
                        else:
                            document_name = f"{view_name}_export_{timestamp}"
                        
                        # Export from response data
                        excel_file = export_data_from_response(data, document_name, human_readable_headers)
                    else:
                        raise APIException('Unable to get data from view')
                else:
                    # Standard queryset-based export
                    queryset = self.filter_queryset(self.get_queryset())
                    
                    # Generate document name based on model and timestamp
                    model_name = queryset.model.__name__
                    app_label = queryset.model._meta.app_label
                    
                    # Use custom document name if provided, otherwise generate one
                    custom_name = request.GET.get('document_name', '')
                    if custom_name:
                        document_name = f"{custom_name}_{timestamp}"
                    else:
                        document_name = f"{app_label}_{model_name}_export_{timestamp}"
                    
                    model = f'{app_label}.{model_name}'
                    
                    # Get the Excel file as BytesIO object
                    excel_file = export_data(
                        model, [item.id for item in queryset[start:end]],
                        exclude, include_relations, document_name,
                        human_readable_headers, auto_exclude_non_human_fields
                    )
                    
            except Exception as e:
                raise APIException('There is a problem applying filters or getting data.') from e
        
        # Create HTTP response for file download
        response = HttpResponse(
            excel_file.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{document_name}.xlsx"'
        
        return response

    def filter_by_unique(self, queryset):
        return get_unique_queryset(queryset)

    def list(self, request, *args, **kwargs):
        try:
            model_name = self.queryset.model.__name__.lower()
            # for caching purposes
            params = request.query_params.dict()
            cache_for_params = getattr(
                self, 'cache_for_params',
                [{
                    'page': '1',
                    'size': '20',
                    'id_id': self.kwargs.get('id_id', None)
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
        except Exception:
            return super().list(request, *args, **kwargs)


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
