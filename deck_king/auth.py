from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError
from .models.user import User
from .schemas.token import TokenData
from .db import get_db

# to get a string like this run:
# openssl rand -hex 32
# TODO: move this to a .env file
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oath2_scheme = OAuth2PasswordBearer(tokenUrl="users/token") # TODO: remove hardcode "/users/"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str | bytes, hashed_password: str | bytes) -> bool:
  return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str | bytes) -> str:
  return pwd_context.hash(password)

def get_user(username: str, db: Session) -> User | None:
  return db.query(User).filter(User.username == username).first()

def authenticate_user(username: str, password: str, db: Session) -> User | None:
  user = get_user(username, db)
  if not user:
    return None
  if not verify_password(password, user.hashed_password):
    return None
  return user

def create_access_token(data: dict, expires_delta: timedelta) -> str:
  to_encode = data.copy()
  expire = datetime.now(timezone.utc) + expires_delta
  to_encode.update({"exp": expire})
  encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
  return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oath2_scheme)], db: Annotated[Session, Depends(get_db)]) -> User:
  credentials_exception = HTTPException(
    status_code=401,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
  )

  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username: str = payload.get("sub")
    if username is None:
      raise credentials_exception
    
    token_data = TokenData(username=username)

  except JWTError:
    raise credentials_exception

  user = get_user(username=token_data.username, db=db)
  if user is None:
    raise credentials_exception

  return user
