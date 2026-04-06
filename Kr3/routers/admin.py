from fastapi import APIRouter, Depends
from security import get_current_user, require_role

router = APIRouter(tags=["Admin & RBAC"])


@router.get("/public")
async def public_endpoint():
    return {"message": "This is public, no auth required"}


@router.get("/user-resource")
async def user_resource(current_user: dict = Depends(require_role("user"))):
    return {"message": f"Welcome user {current_user['username']}"}


@router.get("/admin-resource")
async def admin_resource(current_user: dict = Depends(require_role("admin"))):
    return {"message": f"Welcome admin {current_user['username']}"}
