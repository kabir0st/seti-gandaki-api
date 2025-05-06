from django.forms import ValidationError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.utils.permissions import IsAuthenticated
from core.utils.viewsets import DefaultViewSet
from system.apis.filtersets.user import UserFilterSet
from system.models import UserBase
from system.serializers.users import (RegisterUserBaseSerializer,
                                      UserBaseSerializer)

from .auth import authenticate_user


class RegisterUserBaseAPI(GenericAPIView):
    serializer_class = RegisterUserBaseSerializer
    permission_classes = [AllowAny]
    http_method_names = ["post", 'get']
    queryset = UserBase.objects.none()

    def post(self, request):
        data = request.data.copy()
        data['is_superuser'] = False
        data['is_staff'] = False
        data['is_verified'] = False

        serializer = self.serializer_class(data=request.data,
                                           context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        token, details = authenticate_user(request.data['phone_number'],
                                           request.data['password'], request)
        return Response({
            "tokens": token,
            "user_details": details
        },
                        status=status.HTTP_201_CREATED)

    def get(self, request):
        return Response('for testing.')


class UserBaseAPI(DefaultViewSet):
    queryset = UserBase.objects.filter().order_by('-id')
    serializer_class = UserBaseSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'uuid'
    search_fields = ["given_name", 'family_name', 'email', 'phone_number']
    filterset_class = UserFilterSet
    http_method_names = ["get", 'patch', 'delete']

    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(id=self.request.user.id)

    def post(self, request):
        raise ValidationError('Wrong API Call')

    @action(methods=['post'], detail=True)
    def update_password(self, request, *args, **kwargs):
        """
        {
            'old_password': <PASSWORD>,
            'password': <PASSWORD>
        }
        """
        obj = self.get_object()
        # admin needs to change password
        # if not obj.check_password(request.data['old_password']):
        #     return ValidationError('Incorrect Old Password.')
        obj.set_password(request.data['password'])
        obj.save()
        return Response({'msg': "Password Updated."})

    @action(methods=['get'], detail=True)
    def verify(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            raise ValidationError(
                'Permission Denied. You are not allowed to verify user.')
        obj = self.get_object()
        obj.is_verified = not obj.is_verified
        obj.save()
        return Response({'msg': 'User Verified.'})

    @action(methods=['get'], detail=True, url_path='toggle-activation')
    def toggle_activation(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            raise ValidationError('Permission Denied. You are not'
                                  ' allowed to deactivate/reactivate user.')
        obj = self.get_object()
        obj.is_active = not obj.is_active
        obj.save()
        return Response({'msg': 'User Verified.'})
