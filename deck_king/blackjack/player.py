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
  def on_update(self, help: str,
                dealer_cards: list[Card],
                states: dict[Player, PlayerState],
                cards: dict[Player, list[Card]],
                pot: dict[Player, int]) -> None:
    ...

  @abstractmethod
  def on_turn(self, dealer_cards: list[Card], player_cards: list[Card], available_actions: list[PlayerAction]) -> PlayerAction:
    ...

  @abstractmethod
  def get_bet(self) -> int:
    ...
