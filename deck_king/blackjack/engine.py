from fastapi import WebSocket
from ..blackjack.deck import Deck, Card
from ..blackjack.player import PlayerState
from enum import Enum, auto
from ..routers.ws.room import Room

class GameState(Enum):
  BET = auto()
  PLAYING = auto()
  DEALER = auto()
  END = auto()

class Engine:
  def __init__(self):
    self.room = Room(0)
    self.connections: dict[WebSocket, str] = {}
    self.waiting_connections: dict[WebSocket, str] = {}
    self.turn = 0

    self.deck = Deck()
    
    self.game_state: GameState = ...
    self.players_state: dict[WebSocket, PlayerState] = ... 
    self.pots: dict[WebSocket, int] = ...
    self.cards: dict[WebSocket, list[Card]] = ...
    self.dealer_cards: list[Card] = ...

    # self.reset()

  async def reset(self):
    # Add waiting connections to connections
    for ws, username in self.waiting_connections.items():
      self.connections[ws] = username
    self.waiting_connections = {}

    # Reset game state
    self.turn = 0
    self.deck.shuffle()
    self.game_state = GameState.BET
    self.players_state = {ws: PlayerState.PLAYING for ws in self.connections}
    self.pots = {ws: 0 for ws in self.connections}
    self.cards = {ws: [] for ws in self.connections}
    self.dealer_cards = []

    await self.broadcast_state()
    # Send 1st player to bet
    # if len(self.connections) > 0:
      # conn_list = list(self.connections)
      # ws = conn_list[self.turn]
      # await ws.send_json({"turn": self.connections[ws], "action": "bet"})

    print("[INFO] Resetting engine with ", len(self.connections), " players")
    print("[INFO] Connections: ", self.connections)
  
  start = reset

  async def connect(self, websocket: WebSocket, username: str):
    await self.room.connect(websocket)
    self.waiting_connections[websocket] = username
    # Player wont play until next reset

    # If first player, start the game
    if len(self.connections) == 0:
      await self.reset()
  
  def disconnect(self, websocket: WebSocket):
    if websocket == self.websocket:
      self.turn += 1
      if self.turn >= len(self.connections):
        self.turn = 0
    
    self.room.disconnect(websocket)
    del self.connections[websocket]
    # TODO Bug probably, should be replace with a ghost untill reset i feel 
  
  def pause(self, websocket: WebSocket):
    # TODO
    # everything pauses or player just skips until return?
    pass

  @property
  def websocket(self):
    return list(self.connections.keys())[self.turn]
  
  @property
  def state(self) -> dict:
    return {
      "state": str(self.game_state),
      "turn": self.connections[self.websocket],
      "pots": {self.connections[ws]: self.pots[ws] for ws in self.connections},
      # "best": {self.connections[ws]: sum(self.cards[ws]).best() for ws in self.connections},
      "cards": {self.connections[ws]: [card.to_dict() for card in self.cards[ws]] for ws in self.connections},
      "dealer_cards": [card.to_dict() for card in self.dealer_cards],
      "players_state": {self.connections[ws]: str(state) for ws, state in self.players_state.items()}
    }
  
  async def broadcast(self, data):
    await self.room.broadcast(data)

  async def broadcast_state(self):
    await self.broadcast(self.state)

  async def has_blackjack(self, websocket):
    best_value = sum(self.cards[websocket]).best() 
    if best_value == 21:
      return True
    return False

  async def has_busted(self, websocket):
    best_value = sum(self.cards[websocket]).best() 
    if best_value > 21:
      return True
    return False
  
  async def dealer_turn(self):
    await self.broadcast_state()

    # Blackjack policy: while dealer_value < 17, dealer hits
    while sum(self.dealer_cards).best() < 17:
      self.dealer_cards.append(self.deck.draw())
      await self.broadcast_state()

    self.game_state = GameState.END # TODO: USELESS I THINK

    # Compare dealer with player
    # If dealer_value == 21, dealer wins
    # If dealer_value > 21, player wins
    # If player_value > dealer_value, player wins
    # If player_value == dealer_value, draw
    # If player_value < dealer_value, dealer wins

    # Check no player is playing and game is over
    assert (all([self.players_state[ws] != PlayerState.PLAYING for ws in self.connections]) and self.game_state == GameState.END)

    # Dealer's best value
    dealer_value = sum(self.dealer_cards).best()

    # Compare dealer with players
    for ws, username in self.connections.items():
      if self.players_state[ws] == PlayerState.BLACKJACK:
        print(f"[INFO] {username} won with blackjack")
        self.pots[ws] *= 1.5
      elif self.players_state[ws] == PlayerState.BUSTED:
        print(f"[INFO] {username} busted")
        self.pots[ws] = 0
      else:
        # Player's best value
        player_value = sum(self.cards[ws]).best()
        print(f"[INFO] {username} vs dealer: {player_value} vs {dealer_value}")
        print(f"[INFO] {username} pot: {self.pots[ws]}")
        if player_value == dealer_value:
          print(f"[INFO] {username} draw")
          self.pots[ws] = 0
        elif player_value > dealer_value:
          print(f"[INFO] {username} won")
          self.pots[ws] *= 2
        elif player_value < dealer_value:
          self.pots[ws] = 0
          print(f"[INFO] {username} lost")
        else:
          raise Exception("This should not happen")
    
    # await self.broadcast({"state": "END", "pots": {self.connections[ws]: self.pots[ws] for ws in self.connections}})
    await self.broadcast_state()
    await self.reset()
  
  async def feed(self, websocket, data):
    # print(f"[INFO] User: {self.connections[websocket]}, feeding: {data}")
    if websocket != self.websocket:
      # print(f"[INFO] {self.connections[websocket]} Not your turn")
      return

    match self.players_state[websocket]:
      case PlayerState.PLAYING:
        # Game state machine
        match self.game_state:
          case GameState.BET:
            if data["action"] != "bet":
              return # TODO Maybe send error

            print(f"[INFO] {self.connections[websocket]} bet: {data['value']}")
            
            # Place bet
            self.pots[websocket] = data["value"]
            # Draw cards
            self.cards[websocket] = [self.deck.draw(), self.deck.draw()]

            # Check for blackjack or bust
            if await self.has_blackjack(websocket):
              print(f"[INFO] {self.connections[websocket]} has blackjack")
              self.players_state[websocket] = PlayerState.BLACKJACK
            elif await self.has_busted(websocket):
              print(f"[INFO] {self.connections[websocket]} has busted")
              self.players_state[websocket] = PlayerState.BUSTED

            # Pass turn
            self.turn += 1
            # If all players have bet
            if self.turn >= len(self.connections):
              print("[INFO] All players have bet")

              # Finally reveal dealer cards
              self.dealer_cards = [self.deck.draw()] # One is hidden
              # Reset turn
              self.turn = 0

              # Change game state
              if any([self.players_state[ws] == PlayerState.PLAYING for ws in self.connections]):
                self.game_state = GameState.PLAYING
              else: # All players have blackjack or busted
                self.game_state = GameState.DEALER
                await self.dealer_turn()
                return # Don't broadcast state (it's done in dealer_turn)
            
            # Broadcast new state
            await self.broadcast_state()

          case GameState.PLAYING:
            if "action" not in data:
              return # TODO Maybe send error
            
            action = data["action"]

            print(f"[INFO] {self.connections[websocket]} action: {action}")

            match action:
              case "hit":
                # Draw card
                self.cards[websocket].append(self.deck.draw())

                keep_turn = True

                # Check for blackjack or bust
                if await self.has_blackjack(websocket):
                  print(f"[INFO] {self.connections[websocket]} has blackjack")
                  self.players_state[websocket] = PlayerState.BLACKJACK
                  keep_turn = False
                elif await self.has_busted(websocket):
                  print(f"[INFO] {self.connections[websocket]} has busted")
                  self.players_state[websocket] = PlayerState.BUSTED
                  keep_turn = False
                
                if not keep_turn:
                  # Pass turn
                  self.turn += 1
                  # If all players have played
                  if self.turn >= len(self.connections):
                    self.turn = 0
                    self.game_state = GameState.DEALER
                    await self.dealer_turn()
                else:
                  # Broadcast new state
                  await self.broadcast_state()

              case "stand":
                self.players_state[websocket] = PlayerState.STANDING

                # Pass turn
                self.turn += 1
                # If all players have played
                if self.turn >= len(self.connections):
                  self.turn = 0
                  self.game_state = GameState.DEALER
                  await self.dealer_turn()
                else:
                  # Broadcast new state
                  await self.broadcast_state()

              # case "double": # TODO 
              case _:
                return # TODO Maybe send error

          case GameState.DEALER:
            pass # TODO
          case GameState.END:
            pass # TODO

      case PlayerState.STANDING:
        pass # TODO
      case PlayerState.BLACKJACK:
        pass # TODO
      case PlayerState.BUSTED:
        pass # TODO