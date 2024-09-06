from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from Flowershop.center.database import SessionLocal
from Flowershop.center.models import Customer, CustomerLoyalty
from Flowershop.center.routers.auth import get_current_customer

router = APIRouter(
    prefix='/customers',
    tags=['customers']
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
customer_dependency = Annotated[dict, Depends(get_current_customer)]


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


@router.get('/', response_model=CustomerResponse, status_code=status.HTTP_200_OK)
async def get_customer(
        customer: Annotated[dict, Depends(get_current_customer)],
        db: db_dependency
):
    if customer is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    customer_model = db.query(Customer).filter(Customer.customer_id == customer.get('id')).first()

    if customer_model is None:
        raise HTTPException(status_code=404, detail='Customer not found')

    loyal_name = None

    if customer_model.loyalty_id:
        loyalty_model = db.query(CustomerLoyalty).filter(
            CustomerLoyalty.loyalty_id == customer_model.loyalty_id).first()
        if loyalty_model:
            loyal_name = loyalty_model.status

    return {
        "customer_id": customer_model.customer_id,
        "name": customer_model.name,
        "email": customer_model.email,
        "address": customer_model.address,
        "total_spent": customer_model.total_spent,
        "loyalty_id": customer_model.loyalty_id,
        "loyal_name": loyal_name
    }


@router.put('/', response_model=CustomerResponse, status_code=status.HTTP_200_OK)
async def update_customer(
        customer: Annotated[dict, Depends(get_current_customer)],
        customer_update: CustomerUpdateRequest,
        db: db_dependency
):
    if customer is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    customer_model = db.query(Customer).filter(Customer.customer_id == customer.get('id')).first()

    if customer_model is None:
        raise HTTPException(status_code=404, detail='Customer not found')

    if customer_update.name:
        customer_model.name = customer_update.name
    if customer_update.email:
        customer_model.email = customer_update.email
    if customer_update.phone_number:
        customer_model.phone_number = customer_update.phone_number
    if customer_update.address:
        customer_model.address = customer_update.address

    loyal_name = None

    if customer_model.loyalty_id:
        loyalty_model = db.query(CustomerLoyalty).filter(
            CustomerLoyalty.loyalty_id == customer_model.loyalty_id).first()
        if loyalty_model:
            loyal_name = loyalty_model.status
    try:
        db.add(customer_model)
        db.commit()
        return {
            "customer_id": customer_model.customer_id,
            "name": customer_model.name,
            "email": customer_model.email,
            "address": customer_model.address,
            "total_spent": customer_model.total_spent,
            "loyalty_id": customer_model.loyalty_id,
            "loyal_name": loyal_name
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail='Internal Server Error')



@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
        customer: Annotated[dict, Depends(get_current_customer)],
        db: db_dependency,
        verification: CustomerVerification
):
    if customer is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    customer_model = db.query(Customer).filter(Customer.customer_id == customer.get('id')).first()

    if customer_model is None:
        raise HTTPException(status_code=404, detail='Customer not found')

    if not bcrypt_context.verify(verification.password, customer_model.hashed_password):
        raise HTTPException(status_code=401, detail='Incorrect password')

    hashed_new_password = bcrypt_context.hash(verification.new_password)
    customer_model.hashed_password = hashed_new_password

    try:
        db.add(customer_model)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail='Internal Server Error')

    return {"message": "Password updated successfully"}
