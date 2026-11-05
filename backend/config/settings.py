"""Settings for the SAIRE-Linked learning content API.

Development defaults are intentionally convenient; production settings MUST be
provided through environment variables, as described in README.
"""
import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# Local backend/.env is optional; real process environment always wins.
load_dotenv(BASE_DIR / ".env", override=False)
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "local-dev-only-change-before-deploy")
if not DEBUG and SECRET_KEY == "local-dev-only-change-before-deploy":
    raise RuntimeError("DJANGO_SECRET_KEY is required in production")

ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "rest_framework", "rest_framework.authtoken", "corsheaders", "courses", "assessments", "mentoring", "learning_twin", "progression", "allauth", "allauth.account", "allauth.socialaccount", "allauth.socialaccount.providers.google", "allauth.socialaccount.providers.github",
]
MIDDLEWARE = [
    "progression.middleware.PrivateLearningResponses",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {"default": dj_database_url.config(
    default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    conn_max_age=600 if os.getenv("DATABASE_URL") else 0,
    conn_health_checks=True,
)}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "en-za"
TIME_ZONE = "Africa/Johannesburg"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "private_media"  # Never expose via public MEDIA_URL.
STORAGES = {"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}, "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Explicit allowlist only: no wildcard, no credentialed cross-origin API access.
CORS_ALLOWED_ORIGINS = [url.strip().rstrip("/") for url in os.getenv(
    "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",") if url.strip()]
CSRF_TRUSTED_ORIGINS = [url.strip().rstrip("/") for url in os.getenv(
    "CSRF_TRUSTED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000"
).split(",") if url.strip()]
CORS_ALLOW_CREDENTIALS = False
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticatedOrReadOnly"],
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.TokenAuthentication", "rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer", "rest_framework.renderers.BrowsableAPIRenderer"],
}
if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "0") == "1"
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# v10: same-origin browser sessions; TokenAuthentication remains available for CLI.
AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend', 'allauth.account.auth_backends.AuthenticationBackend']
LOGIN_REDIRECT_URL = '/dashboard/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
SOCIALACCOUNT_LOGIN_ON_GET = False
SOCIALACCOUNT_EMAIL_AUTHENTICATION = False
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = False
SOCIALACCOUNT_STORE_TOKENS = False
SOCIALACCOUNT_PROVIDERS = {}
for provider in ['google', 'github']:
    client_id = os.getenv(provider.upper() + '_OAUTH_CLIENT_ID', '')
    secret = os.getenv(provider.upper() + '_OAUTH_CLIENT_SECRET', '')
    cfg = {'SCOPE': ['profile', 'email'] if provider == 'google' else ['user:email']}
    if client_id and secret:
        cfg['APP'] = {'client_id': client_id, 'secret': secret, 'key': ''}
    SOCIALACCOUNT_PROVIDERS[provider] = cfg
SAIRE_SUPPLEMENTARY_GRADE_CAP = int(os.getenv('SAIRE_SUPPLEMENTARY_GRADE_CAP', '70'))
if not 1 <= SAIRE_SUPPLEMENTARY_GRADE_CAP <= 100:
    raise RuntimeError('SAIRE_SUPPLEMENTARY_GRADE_CAP must be between 1 and 100')
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS += ['http://localhost:3000', 'http://127.0.0.1:3000'] if DEBUG else []

# Enable only when the backend is reachable exclusively through a trusted proxy.
USE_X_FORWARDED_HOST = os.getenv("DJANGO_USE_X_FORWARDED_HOST", "0") == "1"
