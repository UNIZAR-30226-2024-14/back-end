from pydantic import BaseModel

# See: https://fastapi.tiangolo.com/tutorial/sql-databases/

class UserBase(BaseModel):
  username: str
  email: str

# So that the password wont be returned in the response
class UserCreate(UserBase):
  password: str

class User(UserBase):
  id: int
  is_online: bool = True
  credit: int

  class Config:
    # orm_mode = True renamed to
    from_attributes = True

class UserInDB(User):
  hashed_password: str
