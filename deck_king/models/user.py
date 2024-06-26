from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from ..db import Base

# See: https://fastapi.tiangolo.com/tutorial/sql-databases/

class User(Base):
  __tablename__ = "users"

  id = Column(Integer, primary_key=True, index=True, autoincrement=True, unique=True)
  username = Column(String, unique=True, index=True)
  email = Column(String, unique=True, index=True)
  hashed_password = Column(String)
  is_online = Column(Boolean, default=True)
  credit = Column(Integer, default=0)
