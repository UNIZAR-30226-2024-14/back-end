from typing import Iterable

from.player import Player, PlayerAction, PlayerState
from .deck import *

class Blackjack:
  def __init__(self, players: Iterable[Player]):
    self.players = list(players)
    self.deck = Deck()
    self.deck.shuffle()

    self.player_state: dict[Player, PlayerState] = {player: PlayerState.PLAYING for player in self.players}
    self.pot: dict[Player, int] = {player: 0 for player in self.players}
    self.cards: dict[Player, list[Card]] = {player: [] for player in self.players}
    self.dealer_cards: list[Card] = []

  def reset(self):
    self.deck.reset()

    self.player_state = {player: PlayerState.PLAYING for player in self.players}
    self.pot = {player: 0 for player in self.players}
    self.cards = {player: [] for player in self.players}
    self.dealer_cards = []
  
  @property
  def dealer_value(self):
    return sum(self.dealer_cards).best()

  def __notify_all(self, help: str = ""):
    for player in self.players:
      player.on_update(help, self.dealer_cards, self.player_state, self.cards, self.pot)

  def __available_actions(self, player: Player) -> list[PlayerAction]:
    actions = [PlayerAction.STAND, PlayerAction.HIT]
    return actions
  
  def __play_action(self, player: Player, action: PlayerAction) -> None:
    if action == PlayerAction.HIT:
      self.cards[player].append(self.deck.draw())
    elif action == PlayerAction.STAND:
      self.player_state[player] = PlayerState.STANDING
  
  def run(self):
    # Ask for bets
    for player in self.players:
      self.pot[player] = player.get_bet()

    # Send info to players
    self.__notify_all(help="bets")

    # Deal cards: 2 for each player and 1 for the dealer (irl 2 for the dealer too, but 1 is hidden so to make the code easier we'll just deal 1)
    self.dealer_cards.append(self.deck.draw())
    for player in self.players:
      self.cards[player].append(self.deck.draw())
      self.cards[player].append(self.deck.draw())

    # Send info to players
    self.__notify_all(help="deal cards")

    # For each player:
    #   1. If player has blackjack, give them the pot x1.5, go to next player
    #      If player busts, take their pot, go to next player
    #   2. else, ask for action
    #       - If player stands, go to next player
    #       - If player hits, give them a card and go to step #1
    #       - ... TODO OTHER ACTIONS
    for player in self.players:
      while self.player_state[player] == PlayerState.PLAYING:
        player_value = sum(self.cards[player]).best()
        if player_value == 21:
          print(f"{player} has blackjack")
          self.pot[player] *= 1.5
          self.player_state[player] = PlayerState.BLACKJACK
      
        elif player_value > 21:
          print(f"{player} has busted")
          self.player_state[player] = PlayerState.BUSTED

        else:
          availible_actions = self.__available_actions(player)
          action = player.on_turn(self.dealer_cards, self.cards[player], availible_actions)
          self.__play_action(player, action)

        # Send info to players
        self.__notify_all(help="player turn")

    # Dealer's turn
    #   Reveal hidden card
    self.dealer_cards.append(self.deck.draw())

    # Send info to players
    self.__notify_all(help="reveal dealer card")

    #   If dealer has less than 17, hit until 17 or more
    while (self.dealer_value < 17):
      self.dealer_cards.append(self.deck.draw())
      # Send info to players
      self.__notify_all(help="dealer hit")

    #   If dealer has blackjack, give the pot to the dealer
    if self.dealer_value == 21:
      print("Dealer has blackjack")
      # Take all pots
      for player in self.players:
        self.pot[player] = 0

      # Send info to players
      self.__notify_all(help="dealer blackjack")
      return

    #   If dealer busts, give the pot to the players
    if self.dealer_value > 21:
      print("Dealer busts")
      # Take all pots
      for player in self.players:
        self.pot[player] *= 2 # TODO: Ask if this is correct

      # Send info to players
      self.__notify_all(help="dealer bust")
      return
    
    #   If dealer has more than 17 but less than 21, compare with players
    #   Assert all players are not playing
    assert all(state != PlayerState.PLAYING for state in self.player_state.values())
    for player in self.players:
      if self.player_state[player] == PlayerState.STANDING:
        player_value = sum(self.cards[player]).best()
        if player_value > self.dealer_value:
          print(f"{player} wins")
          # Give the pot
          self.pot[player] *= 2
        elif player_value == self.dealer_value:
          print(f"{player} ties")
          # Give back the pot i.e. do nothing
        else:
          print(f"{player} loses")
          # Take the pot
          self.pot[player] = 0
    
    # Send info to players
    self.__notify_all(help="compare with dealer")
