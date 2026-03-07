from .base import *  # noqa: F401, F403

DEBUG = True

# In development, allow all origins for convenience
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Add session auth for dev login (alongside allauth JWT for production)
REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [  # noqa: F405
    "rest_framework.authentication.SessionAuthentication",
    "allauth.headless.contrib.rest_framework.authentication.JWTTokenAuthentication",
]

# Use console email backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Celery: run tasks synchronously in dev for easier debugging
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
