from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.database import get_db
from app.models.deficiency import User, PredictionHistory
from app.schemas.predict import PredictInput, PredictResponse, PredictionHistoryOut
from app.services.predict_service import PredictionService

router = APIRouter()


@router.post("/", response_model=PredictResponse, status_code=status.HTTP_200_OK)
def predict_deficiency(
    data: PredictInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run deficiency risk predictions for the authenticated user.

    Can accept demographic + physiological attributes in the request body, or
    falls back to the authenticated user's database profile fields.

    Calculates today's food log totals, resolves user profile, runs Random Forest / XGBoost models,
    generates SHAP local feature explanations, and stores history in the database.
    """
    return PredictionService.execute_prediction(db, current_user, data)


@router.get("/history", response_model=list[PredictionHistoryOut])
def get_prediction_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve the authenticated user's past deficiency prediction records.
    """
    records = (
        db.query(PredictionHistory)
        .filter(PredictionHistory.user_id == current_user.id)
        .order_by(PredictionHistory.prediction_date.desc())
        .all()
    )
    return records
