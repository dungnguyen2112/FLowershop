from datetime import datetime
from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

class CustomerRequest(BaseModel):
    name: str = Field(..., min_length=3)
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    phone_number: str = Field(..., min_length=3)
    address: str = Field(..., min_length=3)
    role_id: int = Field(..., ge=1)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Nguyễn Văn A",
                "email": "sacxc@gmail.com",
                "password": "123456",
                "phone_number": "0123456789",
                "address": "Hà Nội",
                "role_id": 1
            }
        }

class Token(BaseModel):
    access_token: str
    token_type: str
class ProductRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    stock_quantity: int = Field(..., ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Rose Bouquet",
                "description": "A beautiful bouquet of red roses",
                "price": 29.99,
                "stock_quantity": 10
            }
        }

class ProductResponse(BaseModel):
    product_id: int
    name: str
    description: Optional[str]
    price: float
    stock_quantity: int

class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None

class CustomerResponse(BaseModel):
    customer_id: int
    name: str
    email: str
    total_spent: float
    loyalty_id: Optional[int]
    loyal_name: Optional[str]

class OrderItemResponse(BaseModel):
    order_item_id: int
    product_id: int
    quantity: int
    price_at_purchase: float
class OrderResponse(BaseModel):
    order_id: int
    customer_id: int
    total_amount: float
    order_date: datetime
    items: List[OrderItemResponse]

class CustomerResponse(BaseModel):
    customer_id: int
    name: str
    email: str
    total_spent: float
    address: Optional[str]
    loyalty_id: Optional[int]
    loyal_name: Optional[str]


class CustomerUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None


class CustomerVerification(BaseModel):
    password: str
    new_password: str = Field(min_length=6)

class OrderItemRequest(BaseModel):
    product_id: int = Field(..., ge=1)
    quantity: int = Field(..., ge=1)


class OrderRequest(BaseModel):
    order_date: Optional[datetime] = Field(default_factory=datetime.utcnow)
    items: List[OrderItemRequest]

    class Config:
        json_schema_extra = {
            "example": {
                "order_date": "2024-08-27T10:00:00Z",
                "items": [
                    {"product_id": 1, "quantity": 2},
                    {"product_id": 2, "quantity": 1}
                ]
            }
        }


class OrderResponse(BaseModel):
    order_id: int
    total_amount: float
    order_date: datetime
    items: List[OrderItemResponse]


class OrderUpdate(BaseModel):
    order_date: Optional[datetime] = None
    items: Optional[List[OrderItemRequest]] = None

class ProductRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    stock_quantity: int = Field(..., ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Rose Bouquet",
                "description": "A beautiful bouquet of red roses",
                "price": 29.99,
                "stock_quantity": 10
            }
        }

class ProductResponse(BaseModel):
    product_id: int
    name: str
    description: Optional[str]
    price: float
    stock_quantity: int

class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None

class DailyRevenueResponse(BaseModel):
    date: datetime
    total_revenue: float

class MonthlyRevenueResponse(BaseModel):
    year: int
    month: int
    total_revenue: float

class YearlyRevenueResponse(BaseModel):
    year: int
    total_revenue: float

