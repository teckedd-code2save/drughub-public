from fastapi import APIRouter

from app.apis.users.routes import router as users_router
from app.apis.products.routes import router as products_router
from app.apis.orders.routes import router as orders_router
from app.apis.auth.routes import router as auth_router


from app.utils.config import settings

api_router = APIRouter()
# api_router.include_router(auth.router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(products_router)
api_router.include_router(orders_router)

# if settings.ENVIRONMENT == "local":
#     api_router.include_router(private.router)
