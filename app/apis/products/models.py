import uuid

from pydantic import EmailStr
from sqlmodel import Field, SQLModel




# Shared properties
class ProductBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on Product creation
class ProductCreate(ProductBase):
    pass


# Properties to receive on Product update
class ProductUpdate(ProductBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Product(ProductBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )


# Properties to return via API, id is always required
class ProductResponse(ProductBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ProductsResponse(SQLModel):
    data: list[ProductResponse]
    count: int