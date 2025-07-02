import os

from .environments import (CHANNEL, DB_NAME, DB_PASSWORD, DB_USERNAME,
                           REDIS_PASSWORD, REDIS_USERNAME, RESOURCE)

# celery setup
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Kathmandu"

# database

SWAGGER_SETTINGS = {
    "DEFAULT_INFO": "app.urls.api_info",
}
REDIS_URL = f"redis://{RESOURCE}:6379/{CHANNEL}"

CELERY_BROKER_URL = REDIS_URL
CELERY_BROKER = REDIS_URL

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        'TIMEOUT': 60,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            'MAX_ENTRIES': 10000,
        }
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}
CACHE_MIDDLEWARE_SECONDS = 60

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": DB_USERNAME,
        "PASSWORD": DB_PASSWORD,
        "HOST": RESOURCE,
        "PORT": 5432,
    }
}

if os.environ.get("GITHUB_WORKFLOW"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "github_actions",
            "USER": "postgres",
            "PASSWORD": "postgres",
            "HOST": "127.0.0.1",
            "PORT": "5432",
        }
    }
