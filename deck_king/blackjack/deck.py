from __future__ import annotations
from typing import Iterable

from enum import Enum, auto
import random

class Suit(Enum):
  HEARTS = auto()
  DIAMONDS = auto()
  CLUBS = auto()
  SPADES = auto()

class CardValue:
  def __init__(self, value: Iterable[int]) -> None:
    self.__value = set(value)
  
  def best(self) -> int:
    return max(filter(lambda x: x <= 21, self.__value), default=min(self.__value))

  def __add__(self, other: CardValue | Card | int) -> CardValue:
    if isinstance(other, int):
      other = CardValue([other])
    else: 
      other = other if isinstance(other, CardValue) else other.card_value

    value = []
    for v1 in self.__value:
      for v2 in other.__value:
        value.append(v1 + v2)
    
    return CardValue(value)
  
  def __radd__(self, other: CardValue | Card | int) -> CardValue:
    return self + other
  
  def __eq__(self, other: CardValue) -> bool:
    return self.__value == other.__value
  
  def __str__(self) -> str:
    return f"CardValue({self.__value})"
  
  def __repr__(self) -> str:
    return str(self)

class Card:
  def __init__(self, suit: Suit, value: int):
    if value < 2 or value > 14:
      raise ValueError("Invalid card value")
    
    self.suit = suit
    self.value = value
    
    self.card_value = CardValue([1, 11]) if value == 14 else CardValue([min(value, 10)])

  def __str__(self) -> str:
    value = self.value if self.value < 11 else {11: "J", 12: "Q", 13: "K", 14: "A"}[self.value]
    return f"{value} of {self.suit.name}"
  
  def to_dict(self) -> dict:
    return {"suit": self.suit.name, "value": self.value, "blackjack_value": self.card_value.best()}
  
  def __repr__(self) -> str:
    return str(self)

  def __add__(self, other: Card | CardValue | int) -> CardValue:
    return self.card_value + other
  
  def __radd__(self, other: Card | CardValue | int) -> CardValue:
    return self + other

  def __eq__(self, other) -> bool:
    return self.suit == other.suit \
       and self.value == other.value 
  
  def __hash__(self) -> int:
    return hash((self.suit, self.value))

class Deck:
  def __init__(self):
    self.cards: list[Card] = []
    self.reset()

  def reset(self):
    self.cards = []
    for suit in [Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS, Suit.SPADES]:
      for value in range(2, 15):
        self.cards.append(Card(suit, value))
    self.shuffle()

  def shuffle(self):
    random.shuffle(self.cards)

  def draw(self) -> Card:
    return self.cards.pop()

  def is_empty(self) -> bool:
    return len(self.cards) == 0

  def __len__(self) -> int:
    return len(self.cards)
