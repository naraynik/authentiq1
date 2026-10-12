from fastapi import APIRouter

router = APIRouter(prefix="/public", tags=["Public Access"])

@router.get("/test")
async def public_test():
    """
    Development/testing endpoint for public unauthenticated access.
    Does not require JWT or user account.
    """
    return {
        "message": "Public test endpoint accessible without authentication",
        "authenticated": False
    }
