from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .db import Base, engine, get_db
from .models.user import User
from .schemas.user import UserCreate

Base.metadata.create_all(engine)

app = FastAPI()

@app.get("/")
def read_root():
  return {"Hello": "World"}

# TODO:
# ESTO HAY QUE REVISARLO Y MIRAR BIEN LA DOCUMENTACION DE FASTAPI Y TAL PERO
# COMO PROOF OF CONCEPT ESTA BIEN
@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
  # TODO: hash the password
  db_user = User(username=user.username, email=user.email, hashed_password=user.password)
  db.add(db_user)
  db.commit()
  db.refresh(db_user)
  return db_user

@app.get("/users/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
  return db.query(User).filter(User.id == user_id).first()