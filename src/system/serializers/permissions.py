from django.contrib.auth.models import Group, Permission
from rest_framework import serializers


class PermissionSerializer(serializers.ModelSerializer):
    app_label = serializers.CharField(source='content_type.app_label')
    model = serializers.CharField(source='content_type.model')

    action = serializers.SerializerMethodField()

    def get_action(self, instance):
        return str(instance.codename).split('_')[0]

    class Meta:
        model = Permission
        exclude = ('content_type', )


class GroupListSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Group
        exclude = ('permissions', )

    def get_users(self, obj):
        return obj.user_set.filter().count()


class GroupSerializer(GroupListSerializer):

    class Meta:
        model = Group
        fields = '__all__'
