from os import getenv, path
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(path.join(BASE_DIR, ".env"))
SECRET_KEY = getenv("SECRET_KEY")

DEBUG = getenv("DEBUG", "False") == "True"

# for all
RESOURCE = getenv('RESOURCE')

# database
DB_USERNAME = getenv("DB_USER")
DB_NAME = getenv("DB_NAME")
DB_PASSWORD = getenv("DB_PASSWORD")

# redis
CHANNEL = getenv("CHANNEL")
REDIS_USERNAME = getenv("REDIS_USERNAME")
REDIS_PASSWORD = getenv("REDIS_PASSWORD")

# bucket
BUCKET_ENDPOINT = getenv("BUCKET_ENDPOINT")
BUCKET_ACCESS_KEY = getenv("BUCKET_ACCESS_KEY")
BUCKET_SECRET_KEY = getenv("BUCKET_SECRET_KEY")

# FONEPAY_KEY = getenv('FONEPAY_KEY')
# FONEPAY_USERNAME = getenv('FONEPAY_USERNAME')
# FONEPAY_PASSWORD = getenv('FONEPAY_PASSWORD')
# FONEPAY_MERCHANT_CODE = getenv('FONEPAY_MERCHANT_CODE')

# email
EMAIL_HOST_USER = getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = getenv('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = "email-smtp.ap-south-1.amazonaws.com"
EMAIL_PORT = 587
