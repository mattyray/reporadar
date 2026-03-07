from .base import *  # noqa: F401, F403

DEBUG = True

# In development, allow all origins for convenience
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Add session auth for dev login (alongside allauth JWT for production)
REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [  # noqa: F405
    "config.auth.CsrfExemptSessionAuthentication",
    "allauth.headless.contrib.rest_framework.authentication.JWTTokenAuthentication",
]

# Use console email backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Celery: run tasks synchronously in dev for easier debugging
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
