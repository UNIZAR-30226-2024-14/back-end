from fastapi import FastAPI
from .db import Base, engine
from .routers import user
from .routers import websockets

from fastapi.middleware.cors import CORSMiddleware

# https://fastapi.tiangolo.com/tutorial/
# https://fastapi.tiangolo.com/python-types/

Base.metadata.create_all(engine)

app = FastAPI()

origins = ["*"]

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(websockets.router)

@app.get("/")
def read_root():
  return {"Hello": "World"}

@app.get("/clean")
def clean_database_debug_only():
  Base.metadata.drop_all(engine)
  Base.metadata.create_all(engine)
  return {"Database": "Cleaned"}
