import os
from pathlib import Path
import cloudinary
import cloudinary.uploader 
import cloudinary.api
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ----------------------------
# SECURITY
# ----------------------------
SECRET_KEY = config('SECRET_KEY', default='your-local-secret-key')
DEBUG = config('DEBUG', default=False, cast=bool)  # Set to False for production

ALLOWED_HOSTS = ["*"]

# ----------------------------
# APPLICATIONS
# ----------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    "cloudinary",
    "cloudinary_storage",

    'app',
    'dashboard',
]


# For Email (Development/Testing)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_SSL = True  # ✅ CORRECT for port 465
EMAIL_USE_TLS = False  # ✅ Must be False when using SSL
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='your-email@gmail.com')  # Your Email
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='your-app-password')  # Email App Password
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='Citadel Markets Pro <support@citadelmarketspro.com>')
ADMIN_NOTIFICATION_EMAIL = config('ADMIN_NOTIFICATION_EMAIL', default='support@citadelmarketspro.com')


FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

# ----------------------------
# CLOUDINARY
# ----------------------------
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': config('CLOUDINARY_API_KEY'),
    'API_SECRET': config('CLOUDINARY_API_SECRET')
}
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

cloudinary.config(
    cloud_name=config("CLOUDINARY_CLOUD_NAME"),
    api_key=config("CLOUDINARY_API_KEY"),
    api_secret=config("CLOUDINARY_API_SECRET"),
)

# ----------------------------
# REST FRAMEWORK
# ----------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}



AUTH_USER_MODEL = "app.CustomUser"




# ----------------------------
# MIDDLEWARE
# ----------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
  
ROOT_URLCONF = 'citadel.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ----------------------------
# DATABASE
# ----------------------------

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
        conn_max_age=600
    )
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

WSGI_APPLICATION = 'citadel.wsgi.application'




# ----------------------------
# STATIC & MEDIA FILES
# ----------------------------
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# CRITICAL FIX: Remove the extra 'static' subdirectory
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = BASE_DIR / 'media'

# Only include STATICFILES_DIRS if the 'static' folder exists
if (BASE_DIR / "static").exists():
    STATICFILES_DIRS = [BASE_DIR / "static"]

# Move STATICFILES_STORAGE after STATIC_ROOT
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# WhiteNoise configuration
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG

# ----------------------------
# CORS
# ----------------------------
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://citadelsmarket.com",
    "https://www.citadelsmarket.com",
    "https://citadelprosmarket.com",
    "https://www.citadelprosmarket.com",
    "http://103.217.253.60",
]

# ----------------------------
# SESSION
# ----------------------------
SESSION_COOKIE_NAME = 'citadelsmarket_session'
SESSION_COOKIE_AGE = 86400 * 30        # 30 days
SESSION_SAVE_EVERY_REQUEST = True       # reset expiry on each request
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://103.217.253.60",
    "https://citadelsmarket.com",
    "https://www.citadelsmarket.com",
    "https://citadelprosmarket.com",
    "https://www.citadelprosmarket.com",
    "https://citadelmarketspro.netlify.app",
    "https://citadelmarketspro.onrender.com",
    "https://citadelprofront.vercel.app",
    "https://www.citadelmarketspro.com",
    "https://citadelmarketspro.com",
    "https://citadelmarketspro.vercel.app",
    "https://citadelmarketspro-nwnb7g7z3-bidaks-projects.vercel.app",
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-frontend-url',  # Add custom header
]
# ----------------------------
# OTHER SETTINGS
# ----------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

