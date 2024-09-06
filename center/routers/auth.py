from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt

from Flowershop.center.database import SessionLocal
from Flowershop.center.models import Customer

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

SECRET_KEY = 'b4546727f59c2e0d8ad3a957f236784f10d5b7c41338b112274084d70c2e16df'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

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

def authenticate_customer(email: str, password: str, db: Session):
    customer = db.query(Customer).filter(Customer.email == email).first()
    if not customer:
        return False
    if not bcrypt_context.verify(password, customer.hashed_password):
        return False
    return customer

def create_access_token(email:str, customer_id: int, role_id: int, expires_delta: timedelta):
    encode = {'sub': email, 'id': customer_id, 'role': role_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_customer(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get('sub')
        customer_id: int = payload.get('id')
        role_id: int = payload.get('role')
        if email is None or customer_id is None:
            raise HTTPException(status_code=401, detail='Could not validate credentials')
        return {'name': email, 'id': customer_id, 'role': role_id}
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f'JWT Error: {str(e)}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Unexpected Error: {str(e)}')


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_customer(db: db_dependency,
                          create_customer_request: CustomerRequest):
    try:
        existing_customer = db.query(Customer).filter(Customer.email == create_customer_request.email).first()
        if existing_customer:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_password = bcrypt_context.hash(create_customer_request.password)
        create_customer_model = Customer(
            name=create_customer_request.name,
            email=create_customer_request.email,
            hashed_password=hashed_password,
            phone_number=create_customer_request.phone_number,
            address=create_customer_request.address,
            role_id=create_customer_request.role_id
        )
        db.add(create_customer_model)
        db.commit()
        db.refresh(create_customer_model)
        return {"message": "Customer created successfully"}
    except Exception as e:
        print(f'Error in create_customer: {str(e)}')
        raise HTTPException(status_code=500, detail=f'Internal Server Error: {str(e)}')


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: db_dependency):
    try:
        customer = authenticate_customer(form_data.username, form_data.password, db)

        print(f'Authenticated customer: {customer}')

        if not customer:
            print(f'Failed authentication attempt for email: {form_data.username}')
            raise HTTPException(status_code=401, detail='Could not validate credentials')

        token = create_access_token(customer.email, customer.customer_id, customer.role_id, timedelta(minutes=20))
        return {'access_token': token, 'token_type': 'bearer'}

    except Exception as e:
        print(f'Error in login_for_access_token: {str(e)}')
        raise HTTPException(status_code=500, detail=f'Internal Server Error: {str(e)}')


