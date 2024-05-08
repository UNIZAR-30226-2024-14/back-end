from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from ..db import Base

class BJTable(Base):
  __tablename__ = "bjtables"

  id = Column(Integer, primary_key=True, index=True, autoincrement=True, unique=True)
  player1 = Column(Integer, ForeignKey("users.id"), nullable=True)
  player2 = Column(Integer, ForeignKey("users.id"), nullable=True)
  player3 = Column(Integer, ForeignKey("users.id"), nullable=True)
  player4 = Column(Integer, ForeignKey("users.id"), nullable=True)
  player5 = Column(Integer, ForeignKey("users.id"), nullable=True)

  # Derivated field
  @property
  def n_players(self):
    return sum([1 for player in [self.player1, self.player2, self.player3, self.player4, self.player5] if player is not None])
