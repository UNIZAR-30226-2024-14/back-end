from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session
from ..models.bjtable import BJTable
from ..models.user import User
from ..schemas.token import Token
from ..auth import get_current_user
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

@router.post("/create")
async def create_table(db: Session = Depends(get_db)):
  table = BJTable()
  db.add(table)
  db.commit()
  db.refresh(table)
  return {"table_id": table.id}

@router.post("/join/{table_id}")
async def join(table_id: int, user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):
  table = db.query(BJTable).filter(BJTable.id == table_id).first()
  for i in range(4):
    if getattr(table, f"player{i+1}") is None:
      setattr(table, f"player{i+1}", user.id)
      db.commit()
      return {"table_id": table.id}
  raise HTTPException(status_code=400, detail="Table is full")

@router.post("/leave/{table_id}")
async def leave(table_id: int, user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):
  table = db.query(BJTable).filter(BJTable.id == table_id).first()
  for i in range(4):
    if getattr(table, f"player{i+1}") == user.id:
      setattr(table, f"player{i+1}", None)
      db.commit()
      return {"success": True}
  raise HTTPException(status_code=400, detail="User is not in table")

@router.post("/delete/{table_id}")
async def delete(table_id: int, user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):
  table = db.query(BJTable).filter(BJTable.id == table_id).first()
  if table.n_players == 0:
    db.delete(table)
    db.commit()
    return {"success": True}
  raise HTTPException(status_code=400, detail="Users still in table")

@router.post("/search") # This should be a GET request TODO
async def search(db: Session = Depends(get_db)):
  # Search for a table
  table = db.query(BJTable).filter(BJTable.n_players < 4).order_by(desc(BJTable.n_players)).first()
  if table:
    return {"table_id": table.id}
  else:
    raise HTTPException(status_code=404, detail="No tables found")
