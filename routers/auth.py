"""
OAuth 2.0 Authorization Router for Gmail API
"""

import os
from fastapi import APIRouter, HTTPException
from services.gmail_service import gmail_service
from utils.logger import logger

router = APIRouter(prefix="/auth", tags=["Google OAuth"])


@router.get("/status")
def get_auth_status():
    """
    Check if valid Gmail OAuth token is saved locally.
    """
    has_token = os.path.exists(gmail_service.token_file)
    has_creds = os.path.exists(gmail_service.credentials_file)

    if not has_creds:
        return {
            "authorized": False,
            "status": "missing_credentials",
            "message": "Missing credentials.json from Google Cloud Console. Place credentials.json in project root."
        }

    if has_token:
        try:
            gmail_service.get_credentials()
            return {"authorized": True, "status": "active", "message": "Gmail OAuth credentials authorized & active."}
        except Exception as e:
            return {"authorized": False, "status": "token_expired", "message": f"Token error: {e}"}

    return {"authorized": False, "status": "needs_authorization", "message": "Call /auth/authorize to authorize Gmail."}


@router.get("/authorize")
def authorize_gmail():
    """
    Triggers Google OAuth authorization flow.
    """
    try:
        creds = gmail_service.get_credentials()
        return {"status": "success", "message": "Gmail OAuth authorization completed successfully."}
    except Exception as e:
        logger.error(f"OAuth error: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth Authorization failed: {str(e)}")
