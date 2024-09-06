from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from Flowershop.center import models
from Flowershop.center.database import SessionLocal
from Flowershop.center.models import Order
from Flowershop.center.routers.Basemodel import DailyRevenueResponse, MonthlyRevenueResponse, YearlyRevenueResponse
from Flowershop.center.routers.auth import get_current_customer

router = APIRouter(
    prefix='/revenue',
    tags=['revenue']
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def admin_required(current_user: dict):
    if current_user['role'] != 1:
        raise HTTPException(status_code=403, detail="You do not have sufficient permissions")


@router.get("/statistics/daily", response_model=DailyRevenueResponse)
def get_daily_revenue(
    date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_customer)
):
    admin_required(current_user)
    query = db.query(
        func.date(Order.order_date).label('date'),
        func.sum(Order.total_amount).label('total_revenue')
    )

    if date:
        query = query.filter(func.date(Order.order_date) == date)

    result = query.group_by(
        func.date(Order.order_date)
    ).first()

    if result is None:
        return DailyRevenueResponse(date=date, total_revenue=0.0)

    return DailyRevenueResponse(date=result.date, total_revenue=result.total_revenue)


@router.get("/statistics/monthly", response_model=MonthlyRevenueResponse)
def get_monthly_revenue(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_customer)
):
    admin_required(current_user)
    query = db.query(
        func.extract('year', Order.order_date).label('year'),
        func.extract('month', Order.order_date).label('month'),
        func.sum(Order.total_amount).label('total_revenue')
    )

    if year:
        query = query.filter(func.extract('year', Order.order_date) == year)
    if month:
        query = query.filter(func.extract('month', Order.order_date) == month)

    result = query.group_by(
        func.extract('year', Order.order_date),
        func.extract('month', Order.order_date)
    ).first()

    if result is None:
        return MonthlyRevenueResponse(year=year or 0, month=month or 0, total_revenue=0.0)

    return MonthlyRevenueResponse(year=int(result.year), month=int(result.month), total_revenue=result.total_revenue)


@router.get("/statistics/yearly", response_model=YearlyRevenueResponse)
def get_yearly_revenue(
    year: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_customer)
):
    admin_required(current_user)
    query = db.query(
        func.extract('year', Order.order_date).label('year'),
        func.sum(Order.total_amount).label('total_revenue')
    )

    if year:
        query = query.filter(func.extract('year', Order.order_date) == year)

    result = query.group_by(
        func.extract('year', Order.order_date)
    ).first()

    if result is None:
        return YearlyRevenueResponse(year=year or 0, total_revenue=0.0)

    return YearlyRevenueResponse(year=int(result.year), total_revenue=result.total_revenue)
