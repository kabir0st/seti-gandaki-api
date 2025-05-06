import traceback

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms import ValidationError
from django.http import JsonResponse
from rest_framework.exceptions import NotAuthenticated
from rest_framework.exceptions import \
    PermissionDenied as RestFrameworkPermissionDenied
from rest_framework.exceptions import ValidationError as VD
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import exception_handler


def get_user(token):
    user = cache.get(token)
    if user:
        return user
    else:
        return AnonymousUser()


class APIAuthenticationMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        key = request.headers.get("authorization", None)
        if key:
            request.user = get_user(key)
        with transaction.atomic():
            response = self.get_response(request)
        return response


class DisableCSRF(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        setattr(request, "_dont_enforce_csrf_checks", True)
        response = self.get_response(request)
        return response


def core_exception_handler(exc, context):
    response = exception_handler(exc, context)
    msg = exc
    print(traceback.format_exc())
    if isinstance(exc, Exception):
        err_data = {'status': False, 'error': f'{msg}'}
        if isinstance(exc, (PermissionDenied, RestFrameworkPermissionDenied)):
            return JsonResponse(err_data, safe=False, status=403)
        if isinstance(exc, NotAuthenticated):
            return JsonResponse(err_data, safe=False, status=401)
        if isinstance(exc, (ValidationError, VD)):
            try:
                try:
                    error = ' / '.join([
                        f"{key.capitalize()}: {e.capitalize()}"
                        for key in exc.detail for e in exc.detail[key]
                    ])
                except Exception:
                    error = ' / '.join(
                        [f"{key.capitalize()}" for key in exc for e in exc])
            except Exception:
                error = str(exc.detail.get('non_field_errors', exc.detail))
            err_data = {'status': False, 'error': error}
            return JsonResponse(err_data, safe=False, status=400)
        return JsonResponse(err_data, safe=False, status=503)
    return response


class PaginationMiddleware(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'size'
    max_page_size = 100
