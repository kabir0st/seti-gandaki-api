from datetime import timedelta

from .environments import SECRET_KEY

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUTH_HEADER_TYPES": ("authorization", ""),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken", ),
    "TOKEN_TYPE_CLAIM": "token_type",
}

REST_FRAMEWORK = {
    # 'DEFAULT_THROTTLE_CLASSES': [
    #     'rest_framework.throttling.AnonRateThrottle',
    #     'core.utils.throttles.ThrottleMiddleware'
    # ],
    # 'DEFAULT_THROTTLE_RATES': {
    #     'anon': '50/min',
    #     'user': '60/min'
    # },
    "DEFAULT_PERMISSION_CLASSES": ["core.utils.permissions.AppPermission"],
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
    ),
    'ORDERING_PARAM':
    'ordering',
    "DEFAULT_PAGINATION_CLASS":
    "core.utils.middlewares.PaginationMiddleware",
}

REST_FRAMEWORK[
    "EXCEPTION_HANDLER"] = "core.utils.middlewares.core_exception_handler"
