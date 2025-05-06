import contextlib
import os
import random
import re
import string
from decimal import Decimal
from functools import wraps

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


def convert_decimal_to_string(data):
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = convert_decimal_to_string(value)
        return data
    elif isinstance(data, Decimal):
        return str(data)
    else:
        return data


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
                document_name=None):
    if exclude_fields is None:
        exclude_fields = []
    if include_relations is None:
        include_relations = []
    # from users.models.misc import Document
    # document = Document.objects.create(model=model, name=document_name)
    # export_data_task.delay(document.id, ids, exclude_fields,
    # include_relations)
    return 1


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
