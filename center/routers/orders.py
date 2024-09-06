from typing import Annotated, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field
from Flowershop.center import models
from Flowershop.center.database import SessionLocal
from Flowershop.center.models import Order, OrderItem, Product, Customer
from Flowershop.center.routers.Basemodel import OrderRequest, OrderResponse, OrderUpdate, OrderItemResponse
from Flowershop.center.routers.auth import get_current_customer

router = APIRouter(
    prefix='/orders',
    tags=['orders']
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
customer_dependency = Annotated[dict, Depends(get_current_customer)]


def determine_loyalty_id(total_spent: float, db: Session) -> Optional[int]:
    loyalty = db.query(models.CustomerLoyalty).order_by(models.CustomerLoyalty.loyalty_points.desc()).all()
    for level in loyalty:
        if total_spent >= level.loyalty_points:
            return level.loyalty_id
    return None


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=OrderResponse)
def create_order(order: OrderRequest, db: db_dependency, current_customer: customer_dependency):
    try:
        db_customer = db.query(Customer).filter(Customer.customer_id == current_customer['id']).first()
        if not db_customer:
            raise HTTPException(status_code=400, detail="Customer not found")

        total_amount = 0
        order_items = []
        product_ids = [item.product_id for item in order.items]

        products = db.query(Product).filter(Product.product_id.in_(product_ids)).all()
        product_dict = {product.product_id: product for product in products}

        for item in order.items:
            product = product_dict.get(item.product_id)
            if not product:
                raise HTTPException(status_code=400, detail=f"Product ID {item.product_id} not found")
            if product.stock_quantity < item.quantity:
                raise HTTPException(status_code=400, detail=f"Not enough stock for product ID {item.product_id}")
            price_at_purchase = product.price
            total_amount += price_at_purchase * item.quantity
            order_items.append(OrderItem(
                product_id=item.product_id,
                quantity=item.quantity,
                price_at_purchase=price_at_purchase
            ))

        db_order = Order(
            customer_id=current_customer['id'],
            order_date=order.order_date,
            total_amount=total_amount
        )
        db.add(db_order)
        db.commit()
        db.refresh(db_order)

        for item in order_items:
            db_order_item = OrderItem(
                order_id=db_order.order_id,
                product_id=item.product_id,
                quantity=item.quantity,
                price_at_purchase=item.price_at_purchase
            )
            product = db.query(Product).filter(Product.product_id == item.product_id).first()
            product.stock_quantity -= item.quantity
            db.add(db_order_item)

        db.commit()
        db.refresh(db_order)

        # Update customer total_spent and loyalty_id
        db_customer.total_spent += total_amount
        new_loyalty_id = determine_loyalty_id(db_customer.total_spent, db)
        if new_loyalty_id:
            db_customer.loyalty_id = new_loyalty_id
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid customer or product ID")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return db_order


@router.get("/{order_id}", status_code=status.HTTP_200_OK, response_model=OrderResponse)
def get_order(order_id: int, db: db_dependency, current_customer: customer_dependency):
    db_order = db.query(Order).filter(Order.order_id == order_id, Order.customer_id == current_customer['id']).first()
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    return db_order


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(order_id: int, order: OrderUpdate, db: db_dependency, current_customer: customer_dependency):
    try:
        db_order = db.query(Order).filter(Order.order_id == order_id,
                                          Order.customer_id == current_customer['id']).first()
        if db_order is None:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.order_date is not None:
            db_order.order_date = order.order_date

        if order.items is not None:
            existing_items = {item.product_id: item for item in db_order.items}
            new_total_amount = 0

            product_ids = [item.product_id for item in order.items]
            products = db.query(Product).filter(Product.product_id.in_(product_ids)).all()
            product_dict = {product.product_id: product for product in products}

            if len(product_dict) != len(product_ids):
                missing_product_ids = set(product_ids) - set(product_dict.keys())
                raise HTTPException(status_code=400, detail=f"Products with IDs {missing_product_ids} not found")

            for item in order.items:
                product = product_dict[item.product_id]
                price_at_purchase = product.price
                new_total_amount += price_at_purchase * item.quantity

                if item.product_id in existing_items:
                    existing_item = existing_items[item.product_id]
                    existing_item.quantity = item.quantity
                    existing_item.price_at_purchase = price_at_purchase
                else:
                    db_order_item = OrderItem(
                        order_id=db_order.order_id,
                        product_id=item.product_id,
                        quantity=item.quantity,
                        price_at_purchase=price_at_purchase
                    )
                    db.add(db_order_item)

            item_ids_to_keep = {item.product_id for item in order.items}
            for existing_item in db_order.items:
                if existing_item.product_id not in item_ids_to_keep:
                    db.delete(existing_item)

            db_customer = db.query(Customer).filter(Customer.customer_id == current_customer['id']).first()
            db_customer.total_spent -= db_order.total_amount
            db_order.total_amount = new_total_amount
            db_customer.total_spent += new_total_amount
            new_loyalty_id = determine_loyalty_id(db_customer.total_spent, db)
            db_customer.loyalty_id = new_loyalty_id
            db.add(db_customer)

        db.commit()
        db.refresh(db_order)

        order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        order_items_response = [OrderItemResponse(
            order_item_id=item.order_item_id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_purchase=item.price_at_purchase
        ) for item in order_items]

        return OrderResponse(
            order_id=db_order.order_id,
            total_amount=db_order.total_amount,
            order_date=db_order.order_date,
            items=order_items_response
        )

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Integrity error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, db: db_dependency, current_customer: customer_dependency):
    db_order = db.query(Order).filter(Order.order_id == order_id, Order.customer_id == current_customer['id']).first()
    db_customer = db.query(Customer).filter(Customer.customer_id == current_customer['id']).first()
    db_customer.total_spent -= db_order.total_amount
    new_loyalty_id = determine_loyalty_id(db_customer.total_spent, db)
    db_customer.loyalty_id = new_loyalty_id
    db.add(db_customer)
    db.commit()
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    db.delete(db_order)
    db.commit()
    return {}


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[OrderResponse])
def get_all_orders(db: db_dependency, current_customer: customer_dependency):
    orders = db.query(Order).filter(Order.customer_id == current_customer['id']).all()

    order_responses = []
    for order in orders:
        order_items = db.query(OrderItem).filter(OrderItem.order_id == order.order_id).all()
        order_items_response = [
            OrderItemResponse(
                order_item_id=item.order_item_id,
                product_id=item.product_id,
                quantity=item.quantity,
                price_at_purchase=item.price_at_purchase
            )
            for item in order_items
        ]
        order_responses.append(OrderResponse(
            order_id=order.order_id,
            total_amount=order.total_amount,
            order_date=order.order_date,
            items=order_items_response
        ))

    return order_responses
