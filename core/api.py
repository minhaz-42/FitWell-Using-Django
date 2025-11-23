from ninja import NinjaAPI

# Create the API instance
api = NinjaAPI(
    title="NutriAI API",
    version="1.0.0",
    urls_namespace='api'
)

# Import routers after creating the API instance to avoid circular imports
from core.api.nutritionist import router as nutritionist_router

# Register the routers
api.add_router("/nutritionist/", nutritionist_router)

# Ensure the api instance is available for import
__all__ = ['api']