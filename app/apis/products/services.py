import uuid
from typing import Any

from fastapi import HTTPException
from sqlmodel import func, select

from app.utils.database import SessionDep
from models import Product, ProductCreate, ProductsResponse,ProductResponse, ProductUpdate
from app.models import  Message


def read_Products(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve Products.
    """

    if current_user.is_superuser:
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


def read_Product(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> ProductResponse:
    """
    Get Product by ID.
    """
    product = session.get(Product, id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if not current_user.is_superuser and (Product.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return ProductResponse.model_validate(product)


def create_Product(
    *, session: SessionDep, current_user: CurrentUser, Product_in: ProductCreate
) -> Any:
    """
    Create new Product.
    """
    product = Product.model_validate(Product_in, update={"owner_id": current_user.id})
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def update_Product(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    Product_in: ProductUpdate,
) -> Any:
    """
    Update an Product.
    """
    product = session.get(Product, id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if not current_user.is_superuser and (product.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = Product_in.model_dump(exclude_unset=True)
    Product.sqlmodel_update(update_dict)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def delete_Product(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete an Product.
    """
    product = session.get(Product, id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if not current_user.is_superuser and (product.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(product)
    session.commit()
    return Message(message="Product deleted successfully")
