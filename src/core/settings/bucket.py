import os
from typing import List, Tuple

from core.settings.environments import (BASE_DIR, BUCKET_ACCESS_KEY,
                                        BUCKET_ENDPOINT, BUCKET_SECRET_KEY,
                                        USE_BUCKET)

# Determine if bucket storage should be used
# Defaults to False if USE_BUCKET is not set or not 'true'
should_use_bucket = str(USE_BUCKET).lower() == 'true'

if os.environ.get("GITHUB_WORKFLOW") or not should_use_bucket:
    # Use normal storage for GitHub test cases or if USE_BUCKET is false
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
else:
    # Use Minio storage if USE_BUCKET is true and not in a GitHub workflow
    STORAGES = {
        'default': {
            'BACKEND': 'django_minio_backend.models.MinioBackend',
        },
        'staticfiles': {
            'BACKEND': 'django_minio_backend.models.MinioBackendStatic',
        },
    }

    MINIO_ENDPOINT = BUCKET_ENDPOINT
    MINIO_ACCESS_KEY = BUCKET_ACCESS_KEY
    MINIO_SECRET_KEY = BUCKET_SECRET_KEY
    MINIO_USE_HTTPS = True

    MINIO_POLICY_HOOKS: List[Tuple[str, dict]] = [
        ('seti-media', {
            'Version':
            '2012-10-17',
            'Statement': [{
                'Effect': 'Allow',
                'Principal': '*',
                'Action': ['s3:GetObject'],
                'Resource': ['arn:aws:s3:::seti-media/*']
            }, {
                'Effect': 'Allow',
                'Principal': {
                    'AWS': ['arn:aws:iam::account-id:user/user-with-api-key']
                },
                'Action': ['s3:PutObject', 's3:DeleteObject'],
                'Resource': ['arn:aws:s3:::seti-media/*']
            }]
        }),
        ('seti-static', {
            'Version':
            '2012-10-17',
            'Statement': [{
                'Effect': 'Allow',
                'Principal': '*',
                'Action': ['s3:GetObject'],
                'Resource': ['arn:aws:s3:::seti-static/*']
            }, {
                'Effect': 'Allow',
                'Principal': {
                    'AWS': ['arn:aws:iam::account-id:user/user-with-api-key']
                },
                'Action': ['s3:PutObject', 's3:DeleteObject'],
                'Resource': ['arn:aws:s3:::seti-static/*']
            }]
        }),
    ]

    MINIO_PUBLIC_BUCKETS = [
        'seti-static',
        'seti-media',
    ]
    MINIO_PRIVATE_BUCKETS = []

    MINIO_MEDIA_FILES_BUCKET = 'seti-media'
    MINIO_STATIC_FILES_BUCKET = 'seti-static'
    MINIO_BUCKET_CHECK_ON_SAVE = True
    MINIO_CONSISTENCY_CHECK_ON_START = False

    STATIC_URL = '/static/'
    MEDIA_URL = '/media/'
