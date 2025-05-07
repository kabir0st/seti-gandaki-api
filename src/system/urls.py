from django.urls import include, path
from rest_framework.routers import SimpleRouter

from system.apis.auth import (forget_password, login, login_refresh, logout,
                              reset_password, validate_code, whoami)
from system.apis.logs import AuditLogAPI, AuthLogAPI
from system.apis.misc import (FAQAPI, DocumentAPI, GlobalSettingsAPI,
                              InquiriesAPI)
from system.apis.notifications import NotificationViewSet
from system.apis.users import RegisterUserBaseAPI, UserBaseAPI

router = SimpleRouter()

router.register('users', UserBaseAPI, basename='Users')
router.register('documents', DocumentAPI, basename='Documents')
router.register('faqs', FAQAPI, basename='FAQs')
router.register('logs/authentication',
                AuthLogAPI,
                basename='AuthenticationLogs')
router.register('logs', AuditLogAPI, basename='AuditLogs')
router.register('notifications', NotificationViewSet, basename='Notifications')
router.register('global-settings',
                GlobalSettingsAPI,
                basename='GlobalSettings')
router.register('inquiries', InquiriesAPI, basename='Inquiries')

urlpatterns = [
    path('users/register/',
         RegisterUserBaseAPI.as_view(),
         name='RegisterUsers'),
    path('auth/login/', login, name='AuthLogin'),
    path('auth/refresh/', login_refresh, name='TokenRefresh'),
    path('auth/logout/', logout, name='AuthLogout'),
    path('auth/password/reset/', reset_password, name='PasswordReset'),
    path('auth/password/forget/', forget_password, name='ForgetPassword'),
    path('auth/password/validate-code/', validate_code, name='ValidateCode'),
    path('auth/whoami/', whoami, name='WhoAmI'),
    path('', include(router.urls)),
]
