from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Match
from schemas import MatchSchema
from typing import List

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/matches", response_model=List[MatchSchema])
def read_matches(db: Session = Depends(get_db)):
    return db.query(Match).order_by(Match.match_datetime).all()
