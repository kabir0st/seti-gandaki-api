import json

from auditlog.models import LogEntry
from rest_framework import serializers

from system.models.log import AuthenticationLog


class LogEntrySerializer(serializers.ModelSerializer):
    actor_details = serializers.SerializerMethodField()
    resources = serializers.SerializerMethodField()
    changes = serializers.SerializerMethodField()
    action = serializers.SerializerMethodField()

    class Meta:
        model = LogEntry
        exclude = ('')

    def get_actor_details(self, obj):
        if obj.actor:
            return {
                'uuid': str(obj.actor.uuid),
                'full_name': f"{obj.actor.given_name} {obj.actor.family_name}",
                'designation': obj.actor.designation
            }
        return {'uuid': None, 'full_name': "System", 'designation': 'System'}

    def get_resources(self, obj):
        return {
            'app_label': obj.content_type.app_label,
            'model': obj.content_type.model
        }

    def get_changes(self, obj):
        return json.loads(obj.changes)

    def get_action(self, obj):
        actions = ['CREATE', 'UPDATE', 'DELETE', 'ACCESS']
        return actions[obj.action]


class AuthLogSerializer(serializers.ModelSerializer):
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = AuthenticationLog
        fields = '__all__'

    def get_user_details(self, obj):
        return {
            'uuid': str(obj.user.uuid),
            'full_name': f"{obj.user.given_name} {obj.user.family_name}",
            'designation': obj.user.designation
        }
