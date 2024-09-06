from datetime import datetime
from typing import List, Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from Flowershop.center import models
from Flowershop.center.database import SessionLocal
from Flowershop.center.routers.Basemodel import ProductRequest, ProductResponse, ProductUpdateRequest, CustomerResponse, \
    OrderResponse
from Flowershop.center.routers.auth import get_current_customer
from Flowershop.center.routers.orders import OrderItemResponse

router = APIRouter(
    prefix='/admin',
    tags=['admin']
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def admin_required(current_user: Annotated[dict, Depends(get_current_customer)]):
    if current_user['role'] != 1:  # Check if role_id is 1 (admin)
        raise HTTPException(status_code=403, detail="You do not have sufficient permissions")


@router.post("/products", status_code=status.HTTP_201_CREATED, response_model=ProductResponse)
def create_product(
    product: ProductRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_customer)]
):
    admin_required(current_user)
    db_product = models.Product(**product.dict())
    try:
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return db_product

@router.get("/products/{product_id}", status_code=status.HTTP_200_OK, response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_customer)]
):
    admin_required(current_user)
    db_product = db.query(models.Product).filter(models.Product.product_id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@router.put("/products/{product_id}", status_code=status.HTTP_200_OK, response_model=ProductResponse)
def update_product(
    product_id: int,
    product: ProductUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_customer)]
):
    admin_required(current_user)
    db_product = db.query(models.Product).filter(models.Product.product_id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    for key, value in product.dict().items():
        if value is not None:
            setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_customer)]
):
    admin_required(current_user)
    db_product = db.query(models.Product).filter(models.Product.product_id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return {}

@router.get("/products", status_code=status.HTTP_200_OK, response_model=List[ProductResponse])
def get_all_products(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_customer)]
):
    admin_required(current_user)
    return db.query(models.Product).all()

@router.get("/customers", status_code=status.HTTP_200_OK, response_model=List[CustomerResponse])
def get_all_customers(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_customer)]
):
    admin_required(current_user)

    customers = db.query(models.Customer).all()

    customer_responses = []
    for customer in customers:
        loyal_name = None
        if customer.loyalty_id:
            loyalty = db.query(models.CustomerLoyalty).filter(models.CustomerLoyalty.loyalty_id == customer.loyalty_id).first()
            if loyalty:
                loyal_name = loyalty.status

        customer_responses.append(CustomerResponse(
            customer_id=customer.customer_id,
            name=customer.name,
            email=customer.email,
            total_spent=customer.total_spent,
            loyalty_id=customer.loyalty_id,
            loyal_name=loyal_name
        ))

    return customer_responses

@router.get("/orders", status_code=status.HTTP_200_OK, response_model=List[OrderResponse])
def get_all_orders(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_customer)]
):
    admin_required(current_user)
    return db.query(models.Order).all()
