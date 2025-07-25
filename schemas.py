from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class MatchSchema(BaseModel):
    home_team: str
    away_team: str
    match_datetime: datetime
    competition: str

    class Config:
        orm_mode = True


class TicketOrderCreate(BaseModel):
    nama: str
    status: str
    id_card: Optional[str] = None
    jumlah: int
    whatsapp: str