
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models.bjtable import BJTable
from ..models.user import User
from ..schemas.token import Token
from ..db import get_db

router = APIRouter(
  prefix="/bj",
  tags=["blackjack"],
  dependencies=[],
  responses={404: {"description": "Not found"}},
)

@router.get("/tables")
async def read_tables(db: Session = Depends(get_db)):
  db_tables = db.query(BJTable).all() 
  return {"tables": db_tables}

# @router.post("/join")
# async def join()

# @router.post("/play")
# async def play():
#   pass