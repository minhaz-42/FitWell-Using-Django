from typing import Any
from ninja import NinjaAPI
from ninja.security import django_auth

# Create API instance with authentication
api = NinjaAPI(
    title="FitWell API",
    version="1.0.0",
)

# Error handlers
@api.exception_handler(Exception)
def handle_unhandled_error(request, exc: Exception) -> dict:
    return {"success": False, "error": str(exc)}
