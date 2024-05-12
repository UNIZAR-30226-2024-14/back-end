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
  PAUSE = auto()

class Engine:
  def __init__(self):
    self.room = Room(0)
    self.connections: dict[WebSocket, str] = {}
    self.waiting_connections: dict[WebSocket, str] = {}
    # self.turn = 0 # TODO: sort by username im done``
    self.turn: list[str] = ...

    self.deck = Deck()

    self.game_state_before_pause = None
    self.players_paused: dict[str, tuple[PlayerState, float, list[Card]]] = {}
    
    self.game_state: GameState = ...
    self.players_state: dict[WebSocket, PlayerState] = ... 
    self.pots: dict[WebSocket, float] = ...
    self.cards: dict[WebSocket, list[Card]] = ...
    self.dealer_cards: list[Card] = ...

    # self.reset()

  def make_turns(self):
    return sorted(self.connections.values())

  async def reset(self):
    # Add waiting connections to connections
    for ws, username in self.waiting_connections.items():
      self.connections[ws] = username
    self.waiting_connections = {}

    # Reset game state
    # self.turn = 0
    self.turn = self.make_turns()
    self.deck.shuffle()
    self.game_state = GameState.BET
    self.players_state = {ws: PlayerState.PLAYING for ws in self.connections}
    self.pots = {ws: 0.0 for ws in self.connections}
    self.cards = {ws: [] for ws in self.connections}
    self.dealer_cards = []

    await self.broadcast_state()

    print("[INFO] Resetting engine with ", len(self.connections), " players")
    print("[INFO] Connections: ", self.connections)
  
  start = reset

  async def connect(self, websocket: WebSocket, username: str):
    await self.room.connect(websocket)

    if username in self.players_paused: # TODO: test test test
      print(f"[INFO] {username} is back")
      self.connections[websocket] = username
      self.turn = self.make_turns()
      self.players_state[websocket], self.pots[websocket], self.cards[websocket] = self.players_paused[username]
      del self.players_paused[username]

      if len(self.players_paused) == 0:
        print("[INFO] All players are back! Resuming game...")
        self.resume()
    else:
      # Player wont play until next reset
      self.waiting_connections[websocket] = username

    # If first player, start the game
    if len(self.connections) == 0:
      await self.reset()
    else:
      await self.broadcast_state() # TODO: causes some bugs (4)
  
  def disconnect(self, websocket: WebSocket):
    # if websocket == self.websocket: # TODO: might not work
      # self.turn += 1
      # if self.turn >= len(self.connections):
      #   self.turn = 0
    username = self.connections[websocket]
    del self.turn[self.turn.index(username)]
    
    self.room.disconnect(websocket)
    del self.connections[websocket]
    del self.pots[websocket]
    del self.cards[websocket]
    del self.players_state[websocket]
  
  async def pause(self, websocket: WebSocket):
    # Save state
    self.game_state_before_pause = self.game_state
    # Change game state
    self.game_state = GameState.PAUSE

    # Save player
    username = self.connections[websocket]
    if username in self.players_paused:
      raise Exception("Player already paused")
    self.players_paused[username] = (self.players_state[websocket], self.pots[websocket], self.cards[websocket])

    # # websocket is going to disconnect
    # self.room.disconnect(websocket)

    # # Also remove from connections
    # del self.connections[websocket] # TODO Bug probably

    await self.broadcast_state()

  def resume(self):
    if len(self.players_paused) > 0:
      return # All players must be back

    # Restore state
    self.game_state = self.game_state_before_pause

  @property
  def websocket(self):
    # return list(self.connections.keys())[self.turn]
    print("========================================")
    conn_inv = {v: k for k, v in self.connections.items()}
    print(self.turn)
    print(conn_inv)
    return conn_inv[self.turn[0]]
  
  @property
  def paused(self):
    return self.game_state == GameState.PAUSE
  
  @property
  def state(self) -> dict:
    print(self.connections)
    print(self.pots)
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
    print("[INFO] Broadcasting state:", self.state)
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
    
    print(f"[INFO] {self.connections[websocket]} feeding: {data}")
    if "action" in data and data["action"] == "pause":
      await self.pause(websocket)
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
            self.pots[websocket] = float(data["value"])
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
            # self.turn += 1
            self.turn.pop(0)
            # If all players have bet
            # if self.turn >= len(self.connections):
            if len(self.turn) == 0:
              print("[INFO] All players have bet")

              # Finally reveal dealer cards
              self.dealer_cards = [self.deck.draw()] # One is hidden
              # Reset turn
              # self.turn = 0
              self.turn = self.make_turns()

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
                
                if not keep_turn: # self.players_state[websocket] != PlayerState.PLAYING:
                  # Pass turn
                  # self.turn += 1
                  self.turn.pop(0)
                  # If all players have played
                  # if self.turn >= len(self.connections):
                  if len(self.turn) == 0:
                    # self.turn = 0
                    self.turn = self.make_turns()
                    self.game_state = GameState.DEALER
                    await self.dealer_turn()
                else:
                  # Broadcast new state
                  await self.broadcast_state()

              case "stand":
                self.players_state[websocket] = PlayerState.STANDING

                # Pass turn
                # self.turn += 1
                self.turn.pop(0)
                # If all players have played
                # if self.turn >= len(self.connections):
                if len(self.turn) == 0:
                  # self.turn = 0
                  self.turn = self.make_turns()
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
          case GameState.PAUSE:
            pass

      case PlayerState.STANDING:
        pass # TODO
      case PlayerState.BLACKJACK:
        pass # TODO
      case PlayerState.BUSTED:
        pass # TODO