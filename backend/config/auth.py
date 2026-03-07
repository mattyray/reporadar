"""CSRF-exempt session authentication for SPA development.

DRF's built-in SessionAuthentication enforces CSRF on every request,
which doesn't work for a React SPA on a different port (localhost:5173
talking to localhost:8000). CORS already controls which origins can
make requests, so CSRF is redundant here.

Only used in development — production uses JWT tokens via allauth.
"""

from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # Skip CSRF check — CORS handles origin validation
