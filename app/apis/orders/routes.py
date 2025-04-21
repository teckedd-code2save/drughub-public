from fastapi import APIRouter, Depends
from app.utils.security import AuthUser, RequireViewOrder, AuthenticatedUser

router = APIRouter(prefix="/orders", tags=["orders"])

@router.get("/")
def get_orders(route_deps:RequireViewOrder):
    return {"orders": ["order1", "order2"], "user": route_deps.id}