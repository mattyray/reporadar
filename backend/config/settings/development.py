from .base import *  # noqa: F401, F403

DEBUG = True

# In development, allow all origins for convenience
CORS_ALLOW_ALL_ORIGINS = True

# Use console email backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Celery: run tasks synchronously in dev for easier debugging
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
