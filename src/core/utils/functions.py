import contextlib
import os
import random
import re
import string
from decimal import Decimal
from functools import wraps
import numbers

import dateutil.parser
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.utils.http import urlencode
from django.utils.text import slugify
from PIL import Image

import os
from copy import deepcopy
from io import BytesIO

import openpyxl
import pandas as pd
from django.apps import apps
from django.db import  models
from django.utils.text import slugify


def convert_decimal_to_string(data):
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = convert_decimal_to_string(value)
        return data
    elif isinstance(data, Decimal):
        return str(data)
    else:
        return data


def to_decimal(value):
    """
    Safely converts a value to a Decimal object.

    Handles None, Decimal, float, and int inputs.
    Converts floats via their string representation to maintain precision.
    """
    if value is None:
        return Decimal('0.00')
    if isinstance(value, Decimal):
        return value
    if isinstance(value, numbers.Real):
        # Convert float to string first to avoid precision issues
        return Decimal(str(value))
    try:
        return Decimal(value)
    except Exception:
        return Decimal('0.00')


def clean_data(keys, data):
    for key in keys:
        data.pop(key, None)
    return data


def get_cache_key(model_name, params):
    query_string = urlencode(params, doseq=True)
    return f'{model_name}_list_{query_string}'


def get_or_set_cache(model_name, params):
    cache_key = get_cache_key(model_name, params)
    cached_data = cache.get(cache_key, None)
    return cached_data, cache_key


def invalidate_cache(model_name):
    pattern = f'{model_name}_list_*'
    cache.delete_pattern(pattern)


def unique_substring():
    timestamp_part = timezone.now().strftime('%y%m%d-%H%M')
    random_part = ''.join(
        random.choices(string.ascii_uppercase + string.digits, k=1))
    return f'{timestamp_part}-{random_part}'


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def is_token_valid(token):
    return cache.has_key(token)


def get_properties(model, obj):
    property_values = {
        prop_name: getattr(obj, prop_name)
        for prop_name in dir(model)
        if isinstance(getattr(model, prop_name, None), property)
    }
    return property_values


def contains_foreign_characters(name):
    special_chars_pattern = re.compile(r'^[a-zA-Z0-9 :]+$')
    return not bool(special_chars_pattern.search(name))


def default_array():
    return []


def default_json():
    return {}


def get_unique_queryset(queryset, fields_to_check=None):
    if fields_to_check is None:
        fields_to_check = ['id']
    with contextlib.suppress(Exception):
        distinct_filters = Q()
        for field_name in fields_to_check:
            distinct_filters |= Q(**{f"{field_name}__isnull": False})
        distinct_queryset = queryset.filter(distinct_filters).distinct('id')
        distinct_ids = distinct_queryset.values_list('id', flat=True)
        queryset = queryset.model.objects.filter(id__in=distinct_ids)
        return queryset
    return queryset


def validate_name(name):
    if not slugify(name):
        random_string = ''.join(
            random.choices(string.ascii_uppercase + string.ascii_lowercase +
                           string.digits,
                           k=6))
        return f'{name}-{random_string}'
    return name


def grab_error(func):

    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except Exception as exp:
            return JsonResponse(
                {
                    'status': False,
                    'error': f'{exp.__class__.__name__}: {exp}'
                },
                status=503)

    return wrapper


def limit_size(value):
    limit = 30 * 1024 * 1024
    if value.size > limit:
        raise ValidationError('File too large. Size should not exceed 10 MiB.')


def validate_order_by(model, order_by):
    if model:
        valid_orders = [field.name for field in model._meta.get_fields()]
    if ',' in order_by:
        orders = []
        for order_by_field in order_by.split(','):
            if (order_by_field[1:] not in valid_orders
                    and order_by_field not in valid_orders):
                raise ValidationError(
                    f"{order_by_field} is a Invalid order argument.")
            orders.append(order_by_field)
        return orders
    if order_by[1:] not in valid_orders and order_by not in valid_orders:
        raise ValidationError(f"{order_by} is a Invalid order argument.")
    return order_by


def split_word_for_search(word):
    words = word.split(' ')
    for x in words:
        if x == '':
            words.pop(x)
    return words


def clean_url(url):
    return url[:-1] if url is not None and len(
        url) > 1 and url[-1] == "/" else url


def parse_range(ranges):
    try:
        ranges = str(ranges).replace('[', '').replace(']', '').replace(
            '(', '').replace(')', '')
        ranges = ranges.split(',')
        return {'from': ranges[0], 'upto': ranges[1]}
    except Exception as exp:
        raise ValidationError(
            f'Ranges must be given in [__from__, __upto__]'
            f' or (__from__, __upto__) format. Error: {exp}') from exp


def remove_spaces(statement) -> str:
    return ' '.join(str(statement).split())


def str_to_datetime(datetime_str):
    return dateutil.parser.parse(datetime_str)


def is_equal(obj1, obj2, exclude):
    d1, d2 = obj1.__dict__, obj2.__dict__
    return not any(
        (k not in exclude or k not in
         ['_state', '_django_cleanup_original_cache']) and v != d2[k]
        for k, v in d1.items())


def is_equal_include(obj1, obj2, include):
    d1, d2 = obj1.__dict__, obj2.__dict__
    return not any(
        (k in include or k not in ['_state', '_django_cleanup_original_cache'])
        and v != d2[k] for k, v in d1.items())


def export_data(model,
                ids,
                exclude_fields=None,
                include_relations=None,
                document_name=None,
                human_readable_headers=True,
                auto_exclude_non_human_fields=True):
    """
    Enhanced export data function with human-readable headers and smart relationship handling
    
    Args:
        model: Model string in format 'app.ModelName'
        ids: List of object IDs to export
        exclude_fields: List of field names to exclude
        include_relations: List of relationship field names to include
        document_name: Custom document name
        human_readable_headers: Convert field names to human-readable format
        auto_exclude_non_human_fields: Automatically exclude fields not suitable for human reading
    """
    if exclude_fields is None:
        exclude_fields = []
    if include_relations is None:
        include_relations = []
    
    excel_file = extract_field_data(
        model, ids, exclude_fields, include_relations, 
        human_readable_headers, auto_exclude_non_human_fields
    )
    return excel_file


def export_data_from_response(data, document_name=None, human_readable_headers=True):
    """
    Export data from view response (like aggregated stats) and return Excel file as BytesIO object
    """
    
    def _make_column_human_readable(column_name):
        """Convert column name to human-readable format"""
        if not human_readable_headers:
            return column_name
            
        # Convert snake_case to Title Case
        readable_name = str(column_name).replace('_', ' ').title()
        
        # Handle common abbreviations and improve readability
        replacements = {
            'Id': 'ID',
            'Url': 'URL',
            'Api': 'API',
            'Http': 'HTTP',
            'Json': 'JSON',
            'Uuid': 'UUID',
            'Ip': 'IP',
            'Sms': 'SMS',
            'Pdf': 'PDF',
            'Csv': 'CSV',
            'Html': 'HTML',
            'Xml': 'XML',
            'Sql': 'SQL',
        }
        
        for old, new in replacements.items():
            readable_name = readable_name.replace(old, new)
            
        return readable_name
    
    if not data:
        # Create empty DataFrame if no data
        df = pd.DataFrame()
    elif isinstance(data, list):
        # Handle list of dictionaries (most common case)
        df = pd.DataFrame(data)
    elif isinstance(data, dict):
        # Handle single dictionary or nested structure
        if 'results' in data:
            # Handle paginated response
            df = pd.DataFrame(data['results'])
        else:
            # Handle single object or flatten nested dict
            df = pd.DataFrame([data])
    else:
        # Fallback: try to convert to DataFrame
        try:
            df = pd.DataFrame(data)
        except Exception:
            df = pd.DataFrame([{'data': str(data)}])
    
    # Make column headers human-readable
    if not df.empty and human_readable_headers:
        df.columns = [_make_column_human_readable(col) for col in df.columns]
        # Sort columns alphabetically for consistency
        df = df.reindex(sorted(df.columns), axis=1)
    
    # Create Excel file in memory
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        sheet_name = document_name or 'Export'
        df.to_excel(writer,
                    sheet_name=sheet_name,
                    index=False,
                    na_rep='N/A')
        
        # Auto-adjust column widths and apply formatting
        if not df.empty:
            worksheet = writer.sheets[sheet_name]
            
            # Style the header row
            from openpyxl.styles import Font, PatternFill, Alignment
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_alignment = Alignment(horizontal="center", vertical="center")
            
            for col_num, column in enumerate(df.columns, 1):
                # Style header
                cell = worksheet.cell(row=1, column=col_num)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
                
                # Auto-adjust column width
                column_width = max(
                    df[column].astype(str).map(len).max() if not df[column].empty else 0,
                    len(str(column))
                )
                worksheet.column_dimensions[openpyxl.utils.get_column_letter(col_num)].width = min(column_width + 2, 50)
    
    excel_buffer.seek(0)
    return excel_buffer



def boolean_er(value):
    return str(value).capitalize()


def compare_images(image, image_2):
    if image.size != image_2.size:
        return False
    if image.mode != 'RGB':
        image = image.convert('RGB')
    if image_2.mode != 'RGB':
        image_2 = image_2.convert('RGB')
    diff = 0
    for pixel_db, pixel_url in zip(image.getdata(), image_2.getdata()):
        for db_val, url_val in zip(pixel_db, pixel_url):
            diff += abs(db_val - url_val)
    pixels = image.size[0] * image.size[1]
    avg_diff = diff / (3 * pixels)
    similarity_threshold = 10
    return avg_diff <= similarity_threshold


def get_all_exportable_fields(model, depth=0):
    if depth > 2:
        return []
    if not model:
        return []
    exclude_fields_type = [
        models.ManyToOneRel, models.ManyToManyField, models.ImageField,
        models.FileField
    ]
    stable_relations = []
    for field in model._meta.get_fields():
        with contextlib.suppress(Exception):
            if isinstance(field, models.OneToOneRel):
                if hasattr(model, field.name):
                    stable_relations.append(f'{field.name}_details')
                    if getattr(model, field.name):
                        stable_relations = (
                            stable_relations + get_all_exportable_fields(
                                getattr(model, field.name), depth + 1))
            elif not isinstance(field, tuple(exclude_fields_type)):
                if hasattr(model, field.name):
                    stable_relations.append(field.name)
    return list(set(stable_relations))


def optimize_image(image, output_image_path):
    max_size_kb = 120
    desired_ppi = 72
    max_width = 600
    if max(image.size) > max_width:
        ratio = max_width / image.size[1]
        new_size = tuple(int(x * ratio) for x in image.size)
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    width, height = image.size
    width_inch = width / desired_ppi
    height_inch = height / desired_ppi
    image = image.resize((int(width_inch * 72), int(height_inch * 72)),
                         Image.Resampling.LANCZOS)
    characters = string.ascii_letters
    temp_path = ''.join(random.choice(characters) for _ in range(10))
    quality = 100
    image.save(temp_path, 'webp', quality=quality)
    temp_size = os.path.getsize(temp_path)
    while temp_size > (max_size_kb * 1024) and quality > 60:
        quality -= 5
        image.save(temp_path, 'webp', quality=quality)
        temp_size = os.path.getsize(temp_path)
    os.rename(temp_path, output_image_path)
    return output_image_path


def generate_raw_sql(query):
    raw_sql_query = str(query.query)
    params = list(query.query.params)
    final_query = raw_sql_query % tuple(params)
    return str(final_query)


def is_different(current_instance, fields) -> bool:
    '''
    ** MUST BE CALLED FROM pre_save signal **
    Pass the current instance from pre_save,
    this function will compare all fields except the ones in `fields`
    and return True if any of them are different.
    '''
    if not current_instance.pk:
        return False
    old_instance = current_instance.__class__.objects.get(
        id=current_instance.id)
    all_fields = {field.name for field in current_instance._meta.fields}
    fields_to_check = all_fields - set(fields)
    for field in fields_to_check:
        old_value = getattr(old_instance, field, None)
        new_value = getattr(current_instance, field, None)
        if old_value != new_value:
            return True

    return False


def check_if_changed(current_instance, fields) -> bool:
    '''
    ** MUST BE CALLED FROM pre_save signal **
    Pass the current instance from pre_save,
    this function will compare all fields except the ones in `fields`
    and return True if any of them are different.
    '''
    if not current_instance.pk:
        return False
    old_instance = current_instance.__class__.objects.get(
        id=current_instance.id)
    for field in fields:
        old_value = getattr(old_instance, field, None)
        new_value = getattr(current_instance, field, None)
        if old_value != new_value:
            return True

    return False


def optimize_thumbnail(instance):
    if instance.thumbnail_image:
        with contextlib.suppress(Exception):
            image_name = instance.thumbnail_image.name
            if not image_name.endswith('.webp'):
                if "/" in instance.thumbnail_image.name:
                    image_name = instance.thumbnail_image.name.split('/')[-1]
                temp_output_image_path = f"temp_{image_name}"
                with instance.thumbnail_image.open("rb") as image_file:
                    image = Image.open(image_file)
                    optimized_image_path = optimize_image(
                        image, temp_output_image_path)
                with open(optimized_image_path, "rb") as optimized_image_file:
                    instance.thumbnail_image.save(image_name.replace(
                        image_name.split('.')[-1], 'webp'),
                                                  optimized_image_file,
                                                  save=False)
                os.remove(optimized_image_path)
                return instance
def generate_unique_code(model_class, field_name, length=8):
    """
    Generates a unique random code for a given model field.

    Args:
        model_class: The Django model class.
        field_name: The name of the field to check for uniqueness.
        length: The desired length of the code (default is 8).

    Returns:
        A unique random code (string).
    """
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if not model_class.objects.filter(**{field_name: code}).exists():
            return code


def global_model_export(model_class_or_string, 
                       queryset=None,
                       exclude_fields=None,
                       include_relations=None,
                       document_name=None,
                       human_readable_headers=True,
                       auto_exclude_non_human_fields=True,
                       filters=None):
    """
    Global export function that can be used anywhere in the codebase to export model data to Excel.
    
    Args:
        model_class_or_string: Either a Django model class or a string in format 'app.ModelName'
        queryset: Optional queryset to export. If None, exports all objects
        exclude_fields: List of field names to exclude from export
        include_relations: List of relationship field names to include
        document_name: Custom document name for the Excel file
        human_readable_headers: Convert field names to human-readable format
        auto_exclude_non_human_fields: Automatically exclude fields not suitable for human reading
        filters: Dictionary of filters to apply to the queryset (e.g., {'is_active': True})
    
    Returns:
        BytesIO object containing the Excel file
        
    Example usage:
        # Export all active businesses
        excel_file = global_model_export(
            'statements.Business',
            filters={'is_active': True},
            include_relations=['contact_person'],
            document_name='Active_Businesses'
        )
        
        # Export specific queryset
        from statements.models import Business
        businesses = Business.objects.filter(name__icontains='tech')
        excel_file = global_model_export(
            Business,
            queryset=businesses,
            exclude_fields=['registration_number'],
            document_name='Tech_Companies'
        )
    """
    # Handle model class or string
    if isinstance(model_class_or_string, str):
        model_class = apps.get_model(model_class_or_string)
        model_string = model_class_or_string
    else:
        model_class = model_class_or_string
        model_string = f"{model_class._meta.app_label}.{model_class.__name__}"
    
    # Build queryset
    if queryset is None:
        queryset = model_class.objects.all()
    
    # Apply filters if provided
    if filters:
        queryset = queryset.filter(**filters)
    
    # Get IDs from queryset
    ids = list(queryset.values_list('id', flat=True))
    
    if not ids:
        # Return empty Excel file if no data
        return export_data_from_response([], document_name or 'Empty_Export', human_readable_headers)
    
    # Generate document name if not provided
    if not document_name:
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        model_name = model_class._meta.verbose_name_plural.title() if hasattr(model_class._meta, 'verbose_name_plural') else model_class.__name__
        document_name = f"{model_name}_Export_{timestamp}"
    
    # Export the data
    return export_data(
        model_string,
        ids,
        exclude_fields or [],
        include_relations or [],
        document_name,
        human_readable_headers,
        auto_exclude_non_human_fields
    )



def extract_field_data(model, ids, exclude_fields, include_relations, 
                      human_readable_headers=True, auto_exclude_non_human_fields=True):
    """
    Enhanced field data extraction with human-readable headers and smart relationship handling
    """
    
    def _make_human_readable(field_name, field=None):
        """Convert field name to human-readable format"""
        if not human_readable_headers:
            return field_name
            
        # Use verbose_name if available
        if field and hasattr(field, 'verbose_name') and field.verbose_name:
            return str(field.verbose_name).title()
        
        # Convert snake_case to Title Case
        readable_name = field_name.replace('_', ' ').title()
        
        # Handle common abbreviations and improve readability
        replacements = {
            'Id': 'ID',
            'Url': 'URL',
            'Api': 'API',
            'Http': 'HTTP',
            'Json': 'JSON',
            'Uuid': 'UUID',
            'Ip': 'IP',
            'Sms': 'SMS',
            'Pdf': 'PDF',
            'Csv': 'CSV',
            'Html': 'HTML',
            'Xml': 'XML',
            'Sql': 'SQL',
            'Fk': 'Foreign Key',
            'Pk': 'Primary Key',
        }
        
        for old, new in replacements.items():
            readable_name = readable_name.replace(old, new)
            
        return readable_name
    
    def _format_field_value(value, field):
        """Format field value for human readability"""
        if value is None:
            return 'N/A'
        
        # Handle boolean fields
        if isinstance(field, models.BooleanField):
            return 'Yes' if value else 'No'
        
        # Handle choice fields
        if hasattr(field, 'choices') and field.choices:
            # Get display value for choices
            for choice_value, choice_display in field.choices:
                if choice_value == value:
                    return choice_display
        
        # Handle datetime fields
        if isinstance(field, (models.DateTimeField, models.DateField, models.TimeField)):
            if hasattr(value, 'strftime'):
                if isinstance(field, models.DateTimeField):
                    return value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(field, models.DateField):
                    return value.strftime('%Y-%m-%d')
                elif isinstance(field, models.TimeField):
                    return value.strftime('%H:%M:%S')
        
        # Handle decimal fields
        if isinstance(field, models.DecimalField):
            return f"{value:.2f}"
        
        # Handle foreign key relationships
        if isinstance(field, models.ForeignKey):
            if hasattr(value, '__str__'):
                return str(value)
        
        return str(value)
    
    def _should_exclude_field(field, auto_exclude_non_human_fields):
        """Determine if a field should be automatically excluded"""
        if not auto_exclude_non_human_fields:
            return False
            
        # Field types that are not human-readable
        non_human_field_types = [
            models.ManyToOneRel, 
            models.ManyToManyField, 
            models.ImageField,
            models.FileField,
            models.TextField,  # Usually too long for Excel
            models.JSONField,  # Complex data structure
            models.BinaryField,
        ]
        
        # Field names that are typically not human-readable
        non_human_field_names = [
            'password', 'token', 'secret', 'key', 'hash', 'salt',
            'is_superuser', 'is_staff', 'user_permissions', 'groups',
            'last_login', 'date_joined', 'uuid', 'slug'
        ]
        
        # Check field type
        if any(isinstance(field, field_type) for field_type in non_human_field_types):
            return True
            
        # Check field name patterns
        field_name_lower = field.name.lower()
        if any(pattern in field_name_lower for pattern in non_human_field_names):
            return True
            
        return False
    
    def _extract_obj_data(obj, exclude_fields, include_relations):
        """Extract data from a single object with enhanced formatting"""
        stable_relations = deepcopy(include_relations)
        data = {}
        
        for field in obj._meta.get_fields():
            # Skip if explicitly excluded
            if field.name in exclude_fields:
                continue
                
            # Skip if should be auto-excluded
            if _should_exclude_field(field, auto_exclude_non_human_fields):
                continue
            
            # Handle included relations
            if field.name in stable_relations:
                if isinstance(field, (models.ForeignKey, models.OneToOneField)):
                    if hasattr(obj, field.name):
                        related_obj = getattr(obj, field.name)
                        if related_obj:
                            stable_relations.remove(field.name)
                            # Get human-readable representation of related object
                            human_readable_key = _make_human_readable(field.name, field)
                            data[human_readable_key] = str(related_obj)
                            
                elif isinstance(field, models.OneToOneRel):
                    if hasattr(obj, field.name):
                        stable_relations.remove(field.name)
                        related_obj = getattr(obj, field.name)
                        if related_obj:
                            ext = _extract_obj_data(related_obj, exclude_fields, stable_relations)
                            # Prefix related object fields
                            ext = {
                                f'{_make_human_readable(field.name, field)} - {key}': value
                                for key, value in ext.items()
                            }
                            data.update(ext)
            
            # Handle regular fields
            elif not isinstance(field, (models.ManyToOneRel, models.ManyToManyRel)):
                if hasattr(obj, field.name):
                    value = getattr(obj, field.name)
                    formatted_value = _format_field_value(value, field)
                    human_readable_key = _make_human_readable(field.name, field)
                    data[human_readable_key] = formatted_value
                    
        return data

    # Get the model class
    model_class = apps.get_model(model)
    
    # Auto-exclude ID unless explicitly included
    if 'id' not in include_relations and auto_exclude_non_human_fields:
        exclude_fields = list(exclude_fields) + ['id']
    
    # Get objects with select_related for better performance
    objects = model_class.objects.filter(id__in=ids)
    
    # Add select_related for included foreign key relations
    if include_relations:
        fk_relations = []
        for field_name in include_relations:
            try:
                field = model_class._meta.get_field(field_name)
                if isinstance(field, models.ForeignKey):
                    fk_relations.append(field_name)
            except:
                continue
        if fk_relations:
            objects = objects.select_related(*fk_relations)
    
    # Extract data for all objects
    data = []
    for obj in objects:
        try:
            obj_data = _extract_obj_data(obj, exclude_fields, include_relations)
            data.append(obj_data)
        except Exception as e:
            # Log error but continue with other objects
            print(f"Error extracting data for {obj}: {e}")
            continue
    
    # Create DataFrame
    if not data:
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(data)
        
        # Sort columns alphabetically for consistency
        if not df.empty:
            df = df.reindex(sorted(df.columns), axis=1)
    
    # Create Excel file in memory
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        sheet_name = model_class._meta.verbose_name_plural.title() if hasattr(model_class._meta, 'verbose_name_plural') else model_class.__name__
        
        df.to_excel(writer,
                    sheet_name=sheet_name,
                    index=False,
                    na_rep='N/A')
        
        # Auto-adjust column widths and apply formatting
        if not df.empty:
            worksheet = writer.sheets[sheet_name]
            
            # Style the header row
            from openpyxl.styles import Font, PatternFill, Alignment
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_alignment = Alignment(horizontal="center", vertical="center")
            
            for col_num, column in enumerate(df.columns, 1):
                # Style header
                cell = worksheet.cell(row=1, column=col_num)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
                
                # Auto-adjust column width
                column_width = max(
                    df[column].astype(str).map(len).max() if not df[column].empty else 0,
                    len(str(column))
                )
                worksheet.column_dimensions[openpyxl.utils.get_column_letter(col_num)].width = min(column_width + 2, 50)
    
    excel_buffer.seek(0)
    return excel_buffer
