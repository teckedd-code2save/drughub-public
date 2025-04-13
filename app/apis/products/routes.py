import uuid
from typing import Any

from app.apis.products.models import ProductsResponse,Product,ProductResponse,ProductCreate,ProductUpdate
from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.utils.database import SessionDep
from app.utils.security import CurrentUser
from app.models import Message

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=ProductsResponse)
def read_products(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve products.
    """

    if current_user.is_verified:
        count_statement = select(func.count()).select_from(Product)
        count = session.exec(count_statement).one()
        statement = select(Product).offset(skip).limit(limit)
        products = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Product)
            .where(Product.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Product)
            .where(Product.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        products = session.exec(statement).all()

    return ProductsResponse(data=products, count=count)


@router.get("/{id}", response_model=ProductResponse)
def read_product(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get product by ID.
    """
    product = session.get(Product, id)
    if not product:
        raise HTTPException(status_code=404, detail="product not found")
    if not current_user.is_verified and (Product.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return product


@router.post("/", response_model=ProductResponse)
def create_product(
    *, session: SessionDep, current_user: CurrentUser, product_in: ProductCreate
) -> Any:
    """
    Create new product.
    """
    product = Product.model_validate(product_in, update={"owner_id": current_user.id})
    session.add(Product)
    session.commit()
    session.refresh(Product)
    return product


@router.put("/{id}", response_model=ProductResponse)
def update_product(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    product_in: ProductUpdate,
) -> Any:
    """
    Update an product.
    """
    product = session.get(Product, id)
    if not product:
        raise HTTPException(status_code=404, detail="product not found")
    if not current_user.is_verified and (product.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = product_in.model_dump(exclude_unset=True)
    product.sqlmodel_update(update_dict)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.delete("/{id}")
def delete_product(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete an product.
    """
    product = session.get(Product, id)
    if not product:
        raise HTTPException(status_code=404, detail="product not found")
    if not current_user.is_verified and (product.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(product)
    session.commit()
    return Message(message="product deleted successfully")
