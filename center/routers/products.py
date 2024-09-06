from typing import List, Optional, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from Flowershop.center import models
from Flowershop.center.database import SessionLocal
from Flowershop.center.routers.Basemodel import ProductRequest, ProductResponse, ProductUpdateRequest
from Flowershop.center.routers.auth import get_current_customer

router = APIRouter(
    prefix='/products',
    tags=['products']
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

def user_required(current_user: Annotated[dict, Depends(get_current_customer)]):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProductResponse)
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

@router.get("/{product_id}", status_code=status.HTTP_200_OK, response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_customer)]
):
    user_required(current_user)
    db_product = db.query(models.Product).filter(models.Product.product_id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product


@router.put("/{product_id}", status_code=status.HTTP_200_OK, response_model=ProductResponse)
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

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
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

@router.get("/", status_code=status.HTTP_200_OK, response_model=List[ProductResponse])
def get_all_products(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict, Depends(get_current_customer)]
):
    user_required(current_user)
    return db.query(models.Product).all()
