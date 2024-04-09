from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto

from .deck import Card

class PlayerAction(Enum):
  STAND = auto()
  HIT = auto()
  # DOUBLE = auto()
  # SPLIT = auto()
  # INSURANCE = auto()
  # SURRENDER = auto() TODO ASK

class PlayerState(Enum):
  PLAYING = auto()
  STANDING = auto()
  BLACKJACK = auto()
  BUSTED = auto()

class Player(ABC):
  @abstractmethod
  async def on_update(self, help: str,
                      dealer_cards: list[Card],
                      states: dict[Player, PlayerState],
                      cards: dict[Player, list[Card]],
                      pot: dict[Player, int]) -> None:
    ...

  @abstractmethod
  async def on_turn(self, dealer_cards: list[Card], player_cards: list[Card], available_actions: list[PlayerAction]) -> PlayerAction:
    ...

  @abstractmethod
  async def on_end(self) -> None:
    ...

  @abstractmethod
  async def get_bet(self) -> int:
    ...

  @abstractmethod
  def __hash__(self) -> int:
    ...
  
  @abstractmethod
  def __eq__(self, other) -> bool:
    ...

