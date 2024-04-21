from enum import Enum, auto

class PlayerAction(Enum):
  STAND = auto()
  HIT = auto()
  # DOUBLE = auto()
  # SPLIT = auto()
  # INSURANCE = auto()
  # SURRENDER = auto()

class PlayerState(Enum):
  PLAYING = auto()
  STANDING = auto()
  BLACKJACK = auto()
  BUSTED = auto()