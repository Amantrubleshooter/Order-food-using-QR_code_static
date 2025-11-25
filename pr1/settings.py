
########above is my inial hosting code code

"""
LOCAL Development Settings - Uses Aman database on localhost
"""
import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = 'django-insecure-^#ku(-=1nwd8wnfe&1eri+k)_(8g@!n*#p3&!i4=!!c)&rhl3v'
DEBUG = True
ALLOWED_HOSTS = ['*']

# Timezone - CONSISTENT!
USE_TZ = True
TIME_ZONE = 'Asia/Kolkata'

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'cafe',
    'django_crontab',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pr1.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates', 'static'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'pr1.wsgi.application'

# Database - LOCAL PostgreSQL
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'Aman',              # Local database name
#         'USER': 'postgres',          # Local DB username
#         'PASSWORD': '123',           # Local DB password
#         'HOST': 'localhost',         # Local host
#         'PORT': '5432',              # PostgreSQL port
#     }
# }
DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'NAME': 'AmanCafeDB',      # Your MongoDB database name
        'CLIENT': {
            'host': 'mongodb+srv://amanshivhare5657_db_user:l943OjJAfo4dUsYl@cluster0.icwhstl.mongodb.net/Food_qr_static',
            # If MongoDB has username/password -> use:
            # 'host': 'mongodb://<user>:<password>@localhost:27017/?authSource=admin'
        }
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True  # IMPORTANT: Consistent with top!

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files - LOCAL storage
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

# Custom user model
AUTH_USER_MODEL = 'cafe.User'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Cron jobs
CRONJOBS = [
    ('0 */48 * * *', 'django.core.management.call_command', ['cleanup_old_data']),
]

#above is my code for local setting.py

# """
# PRODUCTION Settings for Render using MongoDB (Djongo)
# """

# import os
# from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY = os.environ.get('SECRET_KEY', 'unsafe-secret-key')
# DEBUG = os.environ.get('DEBUG', 'False') == 'True'
# ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# INSTALLED_APPS = [
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',
#     'django.contrib.humanize',
#     'cafe',
#     'django_crontab',
# ]

# MIDDLEWARE = [
#     'django.middleware.security.SecurityMiddleware',
#     'whitenoise.middleware.WhiteNoiseMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
# ]

# ROOT_URLCONF = 'pr1.urls'

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': ['templates', 'static'],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = 'pr1.wsgi.application'

# # ------------------------------------------
# # 🔥 MONGODB CONFIG FOR RENDER (Djongo)
# # ------------------------------------------

# DATABASES = {
#     'default': {
#         'ENGINE': 'djongo',
#         'NAME': 'AmanCafeDB',   # Database name inside MongoDB
#         'CLIENT': {
#             'host': 'mongodb+srv://amanshivhare5657_db_user:l943OjJAfo4dUsYl@cluster0.icwhstl.mongodb.net/Food_qr_static?retryWrites=true&w=majority'
#         }
#     }
# }

# # ------------------------------------------

# AUTH_PASSWORD_VALIDATORS = [
#     {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
# ]

# LANGUAGE_CODE = 'en-us'
# TIME_ZONE = 'Asia/Kolkata'
# USE_I18N = True
# USE_TZ = True

# STATIC_URL = '/static/'
# STATICFILES_DIRS = [BASE_DIR / 'static']
# STATIC_ROOT = BASE_DIR / 'staticfiles'
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# MEDIA_URL = '/media/'
# MEDIA_ROOT = BASE_DIR / 'media'

# AUTH_USER_MODEL = 'cafe.User'
# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CRONJOBS = [
#     ('0 */48 * * *', 'django.core.management.call_command', ['cleanup_old_data']),
# ]

# # Security settings for Render
# if not DEBUG:
#     SECURE_SSL_REDIRECT = True
#     SESSION_COOKIE_SECURE = True
#     CSRF_COOKIE_SECURE = True
#     SECURE_BROWSER_XSS_FILTER = True
#     SECURE_CONTENT_TYPE_NOSNIFF = True
#     X_FRAME_OPTIONS = 'DENY'
