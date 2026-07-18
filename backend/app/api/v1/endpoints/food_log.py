from datetime import datetime, date, time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.deficiency import User, FoodLog
from app.schemas.food_log import FoodLogCreate, FoodLogOut, DailySummary

router = APIRouter()


@router.post("/", response_model=FoodLogOut, status_code=status.HTTP_201_CREATED)
def create_food_log(
    food_in: FoodLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log a new food item and its nutrient metrics for the current user.
    """
    db_log = FoodLog(
        user_id=current_user.id,
        food_name=food_in.food_name,
        quantity=food_in.quantity,
        serving_size=food_in.serving_size,
        meal_type=food_in.meal_type,
        calories=food_in.calories,
        protein=food_in.protein,
        carbohydrates=food_in.carbohydrates,
        fat=food_in.fat,
        iron=food_in.iron,
        calcium=food_in.calcium,
        vitamin_d=food_in.vitamin_d,
        vitamin_b12=food_in.vitamin_b12,
        zinc=food_in.zinc
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


@router.get("/", response_model=List[FoodLogOut])
def list_food_logs(
    date_str: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve logged food items for the current user, optionally filtered by date (YYYY-MM-DD).
    """
    query = db.query(FoodLog).filter(FoodLog.user_id == current_user.id)

    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_datetime = datetime.combine(target_date, time.min)
            end_datetime = datetime.combine(target_date, time.max)
            query = query.filter(
                FoodLog.logged_at >= start_datetime,
                FoodLog.logged_at <= end_datetime
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )

    return query.order_by(FoodLog.logged_at.desc()).all()


@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_food_log(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific food log item.
    """
    food_log = db.query(FoodLog).filter(FoodLog.id == id).first()
    if not food_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food log not found"
        )
    if food_log.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this food log"
        )

    db.delete(food_log)
    db.commit()
    return {"detail": "Food log deleted successfully"}


@router.get("/summary", response_model=DailySummary)
def get_daily_summary(
    date_str: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve the cumulative sum of nutrients for a given date (defaulting to today).
    """
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    else:
        target_date = datetime.utcnow().date()

    start_datetime = datetime.combine(target_date, time.min)
    end_datetime = datetime.combine(target_date, time.max)

    # Perform sum aggregation over database rows
    summary = db.query(
        func.sum(FoodLog.calories).label('calories'),
        func.sum(FoodLog.protein).label('protein'),
        func.sum(FoodLog.carbohydrates).label('carbohydrates'),
        func.sum(FoodLog.fat).label('fat'),
        func.sum(FoodLog.iron).label('iron'),
        func.sum(FoodLog.calcium).label('calcium'),
        func.sum(FoodLog.vitamin_d).label('vitamin_d'),
        func.sum(FoodLog.vitamin_b12).label('vitamin_b12'),
        func.sum(FoodLog.zinc).label('zinc')
    ).filter(
        FoodLog.user_id == current_user.id,
        FoodLog.logged_at >= start_datetime,
        FoodLog.logged_at <= end_datetime
    ).first()

    # Fallback to 0.0 values if no log rows exist (since SUM returns NULL)
    return DailySummary(
        calories=summary.calories or 0.0,
        protein=summary.protein or 0.0,
        carbohydrates=summary.carbohydrates or 0.0,
        fat=summary.fat or 0.0,
        iron=summary.iron or 0.0,
        calcium=summary.calcium or 0.0,
        vitamin_d=summary.vitamin_d or 0.0,
        vitamin_b12=summary.vitamin_b12 or 0.0,
        zinc=summary.zinc or 0.0
    )
