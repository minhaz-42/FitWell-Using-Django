from typing import Any
from ninja import NinjaAPI
from ninja.security import django_auth

# Create API instance with authentication
api = NinjaAPI(
    title="NutriAI API",
    version="1.0.0",
)

# Import routers
from .nutritionist import router as nutritionist_router

# Register routers with API
api.add_router("/nutritionist/", nutritionist_router)

# Error handlers
@api.exception_handler(Exception)
def handle_unhandled_error(request, exc: Exception) -> dict:
    return {"success": False, "error": str(exc)}
