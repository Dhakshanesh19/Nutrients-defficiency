from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_current_user
from app.core.database import get_db
from app.models.deficiency import User
from app.schemas.predict import PredictionHistoryOut

router = APIRouter()

@router.get("/", response_model=List[PredictionHistoryOut])
def get_prediction_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve historical nutrition predictions run by the authenticated user.
    """
    # Real logic: queries `PredictionHistory` model matching `current_user.id`
    # Returning empty list placeholder for structure setup
    return []
