import copy
from rest_framework.permissions import (DjangoModelPermissions)

from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated)


class IsStaffOrReadOnly(IsAuthenticated):

    def has_permission(self, request, view):
        if super().has_permission(request, view):
            if request.method in SAFE_METHODS:
                return True
            return (request.user.is_authenticated and request.user.is_staff)
        return False


class IsStaffOrCreateOnly(IsAuthenticated):

    def has_permission(self, request, view):
        if super().has_permission(request, view):
            if request.method == 'POST':
                return True
            return (request.user.is_authenticated and request.user.is_staff)
        return False


class IsStaff(IsAuthenticated):

    def has_permission(self, request, view):
        if super().has_permission(request, view):
            return request.user.is_staff
        return False


class AppPermission(DjangoModelPermissions):

    def __init__(self):
        self.perms_map = copy.deepcopy(self.perms_map)
        self.perms_map['GET'] = ['%(app_label)s.view_%(model_name)s']

    def internal_check(request, app, model):
        perms_map = {
            'GET': ['%(app_label)s.view_%(model_name)s'],
            'OPTIONS': [],
            'HEAD': [],
            'POST': ['%(app_label)s.add_%(model_name)s'],
            'PUT': ['%(app_label)s.change_%(model_name)s'],
            'PATCH': ['%(app_label)s.change_%(model_name)s'],
            'DELETE': ['%(app_label)s.delete_%(model_name)s'],
        }
        kwargs = {'app_label': app, 'model_name': model}
        if request.method not in perms_map:
            return False
        perms = [perm % kwargs for perm in perms_map[request.method]]
        return request.user.has_perms(perms)
