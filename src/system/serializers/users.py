from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework import serializers

from core.serializers import Base64ImageField
from core.utils.functions import get_properties
from system.models import Notification, UserBase


class LowercaseEmailValidator:

    def __call__(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Enter a valid email address.")
        return value.lower()


class RegisterUserBaseSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=[LowercaseEmailValidator()],
                                   required=False)
    profile_image = Base64ImageField(required=False)
    business_registration = Base64ImageField(required=False)
    verification_document = Base64ImageField(required=False)

    class Meta:
        model = UserBase
        fields = ('email', 'password', 'given_name', 'family_name',
                  'phone_number', 'profile_image', 'is_staff',
                  'business_registration', 'verification_document',
                  'assigned_categories')

        extra_kwargs = {
            'is_active': {
                'read_only': True
            },
            'last_login': {
                'read_only': True
            },
            'password': {
                'write_only': True
            }
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = self.context['request'].user
        if user.is_authenticated:
            validated_data['added_by'] = user
            if not user.is_staff and validated_data['is_staff']:
                raise ValidationError(
                    'You must be a staff member to add another staff.')
            if not user.is_staff:
                validated_data['is_staff'] = False
        else:
            validated_data['is_staff'] = False
        validated_data['is_superuser'] = False
        categories = validated_data.pop('assigned_categories', None)
        instance = self.Meta.model(**validated_data)
        instance.save()
        if password is not None:
            instance.set_password(password)
        if categories:
            instance.assigned_categories.add(*categories)
        instance.save()
        return instance


class MiniUserBaseSerializer(serializers.ModelSerializer):
    properties = serializers.SerializerMethodField(read_only=True)
    name = serializers.SerializerMethodField(read_only=True)
    assigned_categories_details = serializers.SerializerMethodField(
        read_only=True)

    def get_assigned_categories_details(self, obj):
        return obj.assigned_categories.values('id', 'name')

    class Meta:
        model = UserBase
        fields = ('uuid', 'name', 'id', 'given_name', 'family_name',
                  'phone_number', 'created_at', 'updated_at', 'is_staff',
                  'is_active', 'properties', 'profile_image',
                  'assigned_categories_details', 'assigned_categories')

    def get_name(self, obj):
        return f"{obj.given_name} {obj.family_name}"

    def get_properties(self, obj):
        return get_properties(UserBase, obj)


class UserBaseSerializer(MiniUserBaseSerializer):
    properties = serializers.SerializerMethodField(read_only=True)
    added_by_details = MiniUserBaseSerializer(source='added_by',
                                              read_only=True)
    profile_image = Base64ImageField(required=False)
    business_registration = Base64ImageField(required=False)
    verification_document = Base64ImageField(required=False)

    class Meta:
        model = UserBase
        read_only_fields = ('is_active', 'is_staff', 'last_login',
                            'created_at', 'updated_at')
        extra_kwargs = {
            'is_active': {
                'read_only': True
            },
            'last_login': {
                'read_only': True
            },
            'password': {
                'write_only': True
            },
        }
        exclude = ('user_permissions', 'password')

    def get_properties(self, obj):
        return get_properties(UserBase, obj)


class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = '__all__'
