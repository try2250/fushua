"""新手引导 API"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user
from app.models import OnboardingState, User
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/onboarding", tags=["新手引导"])

class AdvanceRequest(BaseModel):
    step: int

@router.get("/state", response_model=ResponseModel[dict])
def get_state(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    os = db.query(OnboardingState).filter(OnboardingState.user_id == current_user.id).first()
    if not os:
        os = OnboardingState(user_id=current_user.id, step=0)
        db.add(os); db.commit()
    return ResponseModel(data={"step": os.step, "user_id": os.user_id})

@router.post("/advance", response_model=ResponseModel[dict])
def advance(req: AdvanceRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if req.step < 0 or req.step > 4:
        raise HTTPException(status_code=400, detail="step must be 0-4")
    os = db.query(OnboardingState).filter(OnboardingState.user_id == current_user.id).first()
    if not os:
        os = OnboardingState(user_id=current_user.id)
        db.add(os)
    os.step = req.step
    db.commit()
    return ResponseModel(data={"step": os.step})
