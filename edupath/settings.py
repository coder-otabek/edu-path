"""edupath/settings.py"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def _get_secret_key():
    key = os.environ.get('SECRET_KEY')
    if key:
        return key
    key_file = BASE_DIR / '.secret_key'
    if key_file.exists():
        return key_file.read_text().strip()
    from django.utils.crypto import get_random_string
    key = 'sk-' + get_random_string(50, 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)')
    key_file.write_text(key)
    return key


SECRET_KEY = _get_secret_key()
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

_allowed = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip().strip("'").strip('"') for h in _allowed.split(',') if h.strip()]

_csrf = os.environ.get('CSRF_TRUSTED_ORIGINS', 'http://127.0.0.1:8000')
CSRF_TRUSTED_ORIGINS = [h.strip().strip("'").strip('"') for h in _csrf.split(',') if h.strip()]

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'accounts',
    'universities',
    'ai_engine',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    *([] if DEBUG else ['whitenoise.middleware.WhiteNoiseMiddleware']),
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.MaintenanceModeMiddleware',
    'core.middleware.OnboardingMiddleware',
]

ROOT_URLCONF = 'edupath.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'edupath.wsgi.application'

# ─── Database ────────────────────────────────────────────────
USE_SQLITE = os.environ.get('USE_SQLITE', 'False') == 'True'

if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME':     os.environ.get('DB_NAME', 'edupath_db'),
            'USER':     os.environ.get('DB_USER', 'edupath_user'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST':     os.environ.get('DB_HOST', 'localhost'),
            'PORT':     os.environ.get('DB_PORT', '5432'),
        }
    }

# ─── Auth ─────────────────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.CustomUser'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── Jazzmin ─────────────────────────────────────────────────
JAZZMIN_SETTINGS = {
    "site_title": "EduPath Admin",
    "site_header": "EduPath",
    "site_brand": "EduPath",
    "welcome_sign": "EduPath boshqaruv paneli",
    "copyright": "EduPath",
    "search_model": ["accounts.CustomUser"],
    "topmenu_links": [
        {"name": "Sayt", "url": "/", "new_window": True},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "order_with_respect_to": [
        "universities", "accounts", "ai_engine", "dashboard", "core",
    ],
    "icons": {
        "accounts.CustomUser":          "fas fa-users",
        "accounts.AbituriyentProfile":  "fas fa-user-graduate",
        "universities.University":      "fas fa-university",
        "universities.Grant":           "fas fa-award",
        "universities.StandaloneGrant": "fas fa-medal",
        "universities.EssaySample":     "fas fa-file-alt",
        "ai_engine.ChatSession":        "fas fa-comments",
        "ai_engine.RoadMap":            "fas fa-map",
        "core.AISettings":              "fas fa-robot",
    },
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": True,
    "use_google_fonts_cdn": False,
    "show_ui_builder": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "cosmo",
    "button_classes": {
        "primary":   "btn-primary",
        "secondary": "btn-secondary",
        "info":      "btn-info",
        "warning":   "btn-warning",
        "danger":    "btn-danger",
        "success":   "btn-success",
    },
}

# ─── Localisation ────────────────────────────────────────────
LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

# ─── Static & Media ──────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── Cache ───────────────────────────────────────────────────
REDIS_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')

if USE_SQLITE or 'test' in sys.argv:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'
else:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
            'TIMEOUT': 3600,
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'

SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 kun

# ─── Email (Gmail SMTP) ──────────────────────────────────────
# USE_SQLITE dan mustaqil — .env da email bo'lsa ishlatadi
EMAIL_HOST          = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT          = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS       = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL  = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'noreply@edupath.uz')

if 'test' in sys.argv:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
elif EMAIL_HOST_USER:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ─── Site URL (email havolalar uchun) ────────────────────────
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000')

# ─── Celery ──────────────────────────────────────────────────
CELERY_BROKER_URL        = REDIS_URL
CELERY_RESULT_BACKEND    = REDIS_URL
CELERY_ACCEPT_CONTENT    = ['json']
CELERY_TASK_SERIALIZER   = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE          = 'Asia/Tashkent'

# ─── Upload limits ───────────────────────────────────────────
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024

# ─── Production security ─────────────────────────────────────
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

SECURE_SSL_REDIRECT = False
# Ngrok uchun
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True