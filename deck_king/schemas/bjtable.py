from pydantic import BaseModel

class BJTable(BaseModel):
  id: int
  player1: int
  player2: int
  player3: int
  player4: int
  n_players: int

  class Config:
    from_attributes = True
