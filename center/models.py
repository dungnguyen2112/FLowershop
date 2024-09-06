from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from Flowershop.center.database import Base


class Customer(Base):
    __tablename__ = 'customers'
    customer_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    address = Column(String, default='')
    loyalty_id = Column(Integer, ForeignKey('customer_loyalty.loyalty_id'), nullable=True)
    total_spent = Column(Float, default=0.0)
    role_id = Column(Integer, ForeignKey('roles.role_id'), nullable=False)

    role = relationship("Role", back_populates="customers")
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    loyalty = relationship("CustomerLoyalty", back_populates="customers")


class CustomerLoyalty(Base):
    __tablename__ = 'customer_loyalty'
    loyalty_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    status = Column(String, nullable=False)
    loyalty_points = Column(Integer, nullable=False)
    loyalty_description = Column(String, nullable=True)

    customers = relationship("Customer", back_populates="loyalty")


class Product(Base):
    __tablename__ = 'products'
    product_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, nullable=False)

    items = relationship("OrderItem", back_populates="product", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = 'orders'
    order_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.customer_id'), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_amount = Column(Float, nullable=False)

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = 'order_items'
    order_item_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.order_id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="items")


class Role(Base):
    __tablename__ = 'roles'
    role_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    role_name = Column(String, nullable=False)
    role_description = Column(String, nullable=True)

    customers = relationship("Customer", back_populates="role")
