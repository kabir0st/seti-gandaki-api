from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from statements.models.settings import StatementSettings
from statements.serializers import StatementSettingsSerializer


class StatementSettingsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        settings = StatementSettings.load()
        serializer = StatementSettingsSerializer(settings)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        settings = StatementSettings.load()
        serializer = StatementSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        return self.put(request, *args, **kwargs)