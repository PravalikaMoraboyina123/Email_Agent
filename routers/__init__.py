"""
FastAPI REST API Routers Package
"""
from routers.auth import router as auth_router
from routers.emails import router as emails_router
from routers.preferences import router as preferences_router
from routers.dashboard import router as dashboard_router
from routers.mobile import router as mobile_router

__all__ = ["auth_router", "emails_router", "preferences_router", "dashboard_router", "mobile_router"]
