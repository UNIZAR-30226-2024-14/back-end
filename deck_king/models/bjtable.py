from sqlalchemy import Column, Integer, String, Integer, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from ..db import Base

class BJTable(Base):
  __tablename__ = "bjtables"

  id = Column(Integer, primary_key=True, index=True, autoincrement=True, unique=True)
  player1 = Column(Integer, ForeignKey("users.id"), nullable=True)
  player2 = Column(Integer, ForeignKey("users.id"), nullable=True)
  player3 = Column(Integer, ForeignKey("users.id"), nullable=True)
  player4 = Column(Integer, ForeignKey("users.id"), nullable=True)

  # Derivated field
  @hybrid_property
  def n_players(self):
    return sum([1 for player in [self.player1, self.player2, self.player3, self.player4] if player is not None])

  @n_players.expression
  def n_players(cls):
    return cls.player1.isnot(None).cast(Integer) + \
           cls.player2.isnot(None).cast(Integer) + \
           cls.player3.isnot(None).cast(Integer) + \
           cls.player4.isnot(None).cast(Integer)
