from rest_framework import serializers

from system.models.misc import FAQ, Document, Inquiries
from system.models.settings import GlobalSettings


class DocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Document
        fields = '__all__'


class FAQSerializer(serializers.ModelSerializer):

    class Meta:
        model = FAQ
        fields = '__all__'


class GlobalSettingsSerializer(serializers.ModelSerializer):

    class Meta:
        model = GlobalSettings
        fields = '__all__'


class InquiriesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Inquiries
        fields = '__all__'
