from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from Flowershop.center.database import Base, engine
from Flowershop.center import models, routers
from Flowershop.center.routers import products, customers, orders, revenuedate, auth, admin

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Include your routers
app.include_router(customers.router)
app.include_router(orders.router)
app.include_router(revenuedate.router)
app.include_router(auth.router)
app.include_router(admin.router)




# Example route
@app.get("/")
def read_root():
    return {"message": "Welcome to the Flower Shop API"}


