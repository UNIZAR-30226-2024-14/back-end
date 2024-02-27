from datetime import timedelta
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from .db import Base, engine
from .schemas.token import Token
from .routers import user
from .auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

# https://fastapi.tiangolo.com/tutorial/
# https://fastapi.tiangolo.com/python-types/

Base.metadata.create_all(engine)

app = FastAPI()

app.include_router(user.router)

@app.get("/")
def read_root():
  # Base.metadata.drop_all(engine)
  return {"Hello": "World"}

# TODO: move to routers/ ?
@app.post("/token", response_model=Token)
async def login_for_access_token(
  form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
  user = authenticate_user(form_data.username, form_data.password)
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