from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..models.user import User
from ..schemas.token import Token
from ..schemas.user import UserCreate
from ..db import get_db
from ..auth import *
import re

# See: https://fastapi.tiangolo.com/tutorial/bigger-applications/

router = APIRouter(
  prefix="/users",
  tags=["users"],
  dependencies=[],
  responses={404: {"description": "Not found"}},
)

EMAIL_REGEX = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"

@router.get("/")
async def read_users(db: Session = Depends(get_db)):
  db_users = db.query(User).all() 
  return {"users": db_users}

@router.post("/register")
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
  db_user = User(username=user.username, email=user.email, hashed_password=hash_password(user.password))

  if not re.match(EMAIL_REGEX, user.email):
    raise HTTPException(status_code=400, detail="Invalid email")

  if db.query(User).filter(User.username == user.username).first():
    raise HTTPException(status_code=400, detail="Username already exists")
  
  if db.query(User).filter(User.email == user.email).first():
    raise HTTPException(status_code=400, detail="Email already exists")
  
  # TODO: future. Check password is strong
  
  db.add(db_user)
  db.commit()
  db.refresh(db_user)

  access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
  access_token = create_access_token(
    data={"sub": user.username}, expires_delta=access_token_expires
  )
  return Token(access_token=access_token, token_type="bearer")

@router.post("/token", response_model=Token)
async def login_for_access_token(
  form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
  db: Session = Depends(get_db)
) -> Token:
  user = authenticate_user(form_data.username, form_data.password, db)
  if not user:
    raise HTTPException(
      status_code=401,
      detail="Incorrect username or password",
      headers={"WWW-Authenticate": "Bearer"},
    )
  
  access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
  access_token = create_access_token(
    data={"sub": user.username}, expires_delta=access_token_expires
  )
  return Token(access_token=access_token, token_type="bearer")