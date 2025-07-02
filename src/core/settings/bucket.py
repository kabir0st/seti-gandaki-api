import os
from typing import List, Tuple

from core.settings.environments import (BASE_DIR, BUCKET_ACCESS_KEY,
                                        BUCKET_ENDPOINT, BUCKET_SECRET_KEY,
                                        USE_BUCKET)


STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
        'LOCATION': os.path.join(BASE_DIR, 'media'),
    },
    'staticfiles': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
        'LOCATION': os.path.join(BASE_DIR, 'staticfiles'),
    },
}

MEDIA_URL = '/media/'
STATIC_URL = '/static/'
