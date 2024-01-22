from pathlib import Path
from os.path import join

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-0y0l*lyvzp0=$mgj55y&_-u%7xfr3=!gpnb(1j0n9fmu!+79$l'

DEBUG = True

if DEBUG: # Only to be used while in developement phase (not be used while pushed into production)
	EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

ALLOWED_HOSTS = []

AUTH_USER_MODEL = 'account.ChatAccount'

AUTHENTICATION_BACKENDS = ( 
    'django.contrib.auth.backends.AllowAllUsersModelBackend', 
    'account.backends.CaseInSensitiveModelBackend',
)

INSTALLED_APPS = [
	'django.contrib.humanize', # This is for the day/date/time formatting

	# Pre-Built apps, Django Default

	'channels', # These 2 are python libraries for upgrading
	'daphne', # connection from HTTP (uni-dir) to WS (bi-dir)

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
	
    # Custom Built apps
    'app',
	'account',
	'friend',
	'chatpublic',
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

ROOT_URLCONF = 'ProChat.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'ProChat.wsgi.application'

ASGI_APPLICATION = 'ProChat.routing.application'

DB_NAME = 'prochat'
DB_USER = 'dbadmin'
DB_PASSWORD = 'passdbadmin'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': 'localhost',
        'PORT': '5433',
    }
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        },
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'


USE_I18N = True

USE_TZ = True

STATICFILES_DIRS = [
    join(BASE_DIR, 'static'),
    join(BASE_DIR, 'media'),
]

STATIC_URL = '/static/'
MEDIA_URL = '/media/'

STATIC_ROOT = join(BASE_DIR, 'static_cdn')
MEDIA_ROOT = join(BASE_DIR, 'media_cdn')

TEMP = join(BASE_DIR, 'media_cdn/temp')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

IMAGE_MAX_UPLOAD_SIZE = 10485760 # 10 * 1024 * 1024 (max size is 10MB)

BASE_URL = 'http://127.0.0.1:8000'
