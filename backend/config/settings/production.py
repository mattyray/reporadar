import os

from .base import *  # noqa: F401, F403

DEBUG = False

# Trust Netlify proxy headers for correct redirect URI construction
USE_X_FORWARDED_HOST = True

# Security
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS — frontend on Netlify, API calls proxied but OAuth redirects are cross-origin
CORS_ALLOW_CREDENTIALS = True

# Whitenoise for static files (no nginx on Railway)
MIDDLEWARE.insert(  # noqa: F405
    MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1,  # noqa: F405
    "whitenoise.middleware.WhiteNoiseMiddleware",
)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Frontend URL (for allauth redirects after OAuth)
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://reporadar.netlify.app")

# After successful OAuth, redirect browser here (relative — goes through Netlify proxy)
LOGIN_REDIRECT_URL = FRONTEND_URL + "/auth/callback"

# Allauth headless frontend URLs
HEADLESS_FRONTEND_URLS = {
    "socialaccount_login_cancelled": FRONTEND_URL + "/login",
    "account_confirm_email": FRONTEND_URL + "/verify-email/{key}",
    "account_reset_password": FRONTEND_URL + "/reset-password",
    "account_reset_password_from_key": FRONTEND_URL + "/reset-password/{key}",
    "account_signup": FRONTEND_URL + "/signup",
}
