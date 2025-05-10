from django.conf import settings as django_setting
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

# from .logics.index import dashboard, login_view

SchemaView = get_schema_view(
    openapi.Info(
        title="Seti Gandaki API",
        default_version='v1',
        description="",
        terms_of_service="",
        contact=openapi.Contact(email=""),
    ),
    public=False,
    permission_classes=[permissions.IsAuthenticated],
)

urlpatterns = [
    path('api/system/', include('system.urls')),
    path('api/statements/', include('statements.urls')),
    path("docs/",
         SchemaView.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),
    path('', admin.site.urls),
]

urlpatterns += static(django_setting.MEDIA_URL,
                      document_root=django_setting.MEDIA_ROOT)
urlpatterns += static(django_setting.STATIC_URL,
                      document_root=django_setting.STATIC_ROOT)
