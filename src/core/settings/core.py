import mimetypes
import os

from .environments import BASE_DIR

APPEND_SLASH = False

ALLOWED_HOSTS = ["*"]

DATA_UPLOAD_MAX_MEMORY_SIZE = 100214400
FILE_UPLOAD_MAX_MEMORY_SIZE = 100214400
DATA_UPLOAD_MAX_NUMBER_FIELDS = 100214400

INSTALLED_APPS = [
    'core.apps.CoreConfig',
    'system',
    'statements',
    'hrm', # Ensure hrm is here, remove fuel app
    # libs
    'daphne',
    'channels',
    'rest_framework_api_key',
    'unfold',
    'unfold.contrib.filters',
    'auditlog',
    'rest_framework',
    'drf_yasg',
    'corsheaders',
    'django_filters',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

if not os.environ.get("GITHUB_WORKFLOW"):
    INSTALLED_APPS.append('django_minio_backend')

MIDDLEWARE = [
    "django.middleware.gzip.GZipMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "core.utils.middlewares.DisableCSRF",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.utils.middlewares.APIAuthenticationMiddleware",
    'auditlog.middleware.AuditlogMiddleware',
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND":
        "django.template.backends.django.DjangoTemplates",
        'DIRS':
        [os.path.join(BASE_DIR, 'build'),
         os.path.join(BASE_DIR, 'template')],
        "APP_DIRS":
        True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME":
        "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator",
    },
    {
        "NAME":
        "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME":
        "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME":
        "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

AUTH_USER_MODEL = "system.UserBase"

TIME_ZONE = "Asia/Kathmandu"

LANGUAGE_CODE = "en-us"

USE_I18N = True

USE_L10N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STATIC_URL = "/static/"

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

CORS_EXPOSE_HEADERS = [
    'data-type',
    'response-properties',
    'Export-Fields',
]

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

mimetypes.add_type("application/javascript", ".js", True)
mimetypes.add_type("text/css", ".css", True)

WHITENOISE_MIMETYPES = {".js": "application/javascript", ".css": "text/css"}

INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]

CKEDITOR_UPLOAD_PATH = "media/ckeditor_uploads/"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.server': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

AUDITLOG_INCLUDE_ALL_MODELS = True
# AUDITLOG_EXCLUDE_TRACKING_MODELS = ("users.VerificationCode", )
ROOT_URLCONF = 'core.urls'

ASGI_APPLICATION = "core.asgi.application"
