from pydantic import BaseModel

class UserBase(BaseModel):
  username: str
  email: str # TODO: maybe phone?

# So that the password wont be returned in the response
class UserCreate(UserBase):
  password: str

class User(UserBase):
  id: int
  # TODO: more fields

  class Config:
    orm_mode = True