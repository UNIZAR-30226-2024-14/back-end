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

    self.broadcast_state()
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
  def is_turn_over(self) -> bool:
    return self.turn >= len(self.connections) - 1 # TODO bug
  
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

  async def blackjack_or_bust(self, websocket):
    best_value = sum(self.cards[websocket]).best() 
    if best_value == 21:
      self.players_state[websocket] = PlayerState.BLACKJACK
      # Tell player
      await websocket.send_json({"turn": self.connections[websocket], "blackjack": True})
      return True
    elif best_value > 21:
      self.players_state[websocket] = PlayerState.BUSTED
      # Tell player
      await websocket.send_json({"turn": self.connections[websocket], "busted": True})
      return True
    return False
  
  async def dealer_turn(self):
    # while dealer_value < 17, hit
    while sum(self.dealer_cards).best() < 17:
      self.dealer_cards.append(self.deck.draw())
      await self.broadcast_state()
    self.game_state = GameState.END
    await self.room.broadcast({"message": "NOW THE POTS ARE BEING DISTRIBUTED! PROBABLY IS WRONG BUT EASY TO FIX!"})

    # Compare dealer with player
    # If dealer_value == 21, dealer wins
    # If dealer_value > 21, player wins
    # If player_value > dealer_value, player wins
    # If player_value == dealer_value, draw
    # If player_value < dealer_value, dealer wins
    assert (all([self.players_state[ws] != PlayerState.PLAYING for ws in self.connections]) and self.game_state == GameState.END)
    dealer_value = sum(self.dealer_cards).best()
    for ws, username in self.connections.items():
      if self.players_state[ws] != PlayerState.BUSTED:
        player_value = sum(self.cards[ws]).best()
        print(f"[INFO] {username} vs dealer: {player_value} vs {dealer_value}")
        print(f"[INFO] {username} pot: {self.pots[ws]}")
        if player_value == dealer_value:
          self.pots[ws] = 0
          print(f"[INFO] {username} draw")
        elif player_value == 21:
          self.pots[ws] *= 1.5
          print(f"[INFO] {username} won with blackjack")
        elif player_value > dealer_value:
          self.pots[ws] *= 2
          print(f"[INFO] {username} won")
        elif player_value < dealer_value:
          self.pots[ws] = 0
          print(f"[INFO] {username} lost")
    
    await self.broadcast_state()
    # TODO: RESET?
    await self.reset()
  
  async def feed(self, websocket, data):
    print(f"[INFO] User: {self.connections[websocket]}, feeding: {data}")
    if websocket != self.websocket:
      print(f"[INFO] {self.connections[websocket]} Not your turn")
      return

    match self.players_state[websocket]:
      case PlayerState.PLAYING:
        # Game state machine
        match self.game_state:
          case GameState.BET:
            if "bet" not in data:
              return # TODO Maybe send error

            print(f"[INFO] {self.connections[websocket]} bet: {data['bet']}")
            
            self.pots[websocket] = data["bet"]
            self.cards[websocket] = [self.deck.draw(), self.deck.draw()]

            if self.is_turn_over:
              print("[INFO] All players have bet")
              self.game_state = GameState.PLAYING
              self.dealer_cards = [self.deck.draw()] # One is hidden

            self.turn += 1
            if self.turn >= len(self.connections):
              self.turn = 0
            # else:
            #   # Send next player to bet
            #   ws = list(self.connections.keys())[self.turn]
            #   await ws.send_json({"turn": self.connections[ws], "action": "bet"})
            
            # Check for blackjack or bust
            if await self.blackjack_or_bust(websocket):
              print("[INFO] Player blackjack or busted busted in bet state")
              # Broadcast new state
              await self.broadcast_state()

              # If only one player, skip to dealer BUG I THINK
              if len(self.connections) == 1:
                self.game_state = GameState.DEALER
                await self.dealer_turn()

              return
            
            # Broadcast new state
            await self.broadcast_state()

            # # Send available actions
            # await self.broadcast_json({"turn": self.connections[websocket], "actions": ["hit", "stand"]})
          case GameState.PLAYING:
            if "action" not in data:
              return # TODO Maybe send error
            
            action = data["action"]

            print("[INFO] Received action: ", action)

            match action:
              case "hit":
                await self.broadcast_json({"turn": self.connections[websocket], "ack": True})

                self.cards[websocket].append(self.deck.draw())

                # Check for blackjack or bust
                if await self.blackjack_or_bust(websocket):
                  print("[INFO] Player blackjack or busted busted in playing state")
                  if self.is_turn_over:
                    self.game_state = GameState.DEALER

                  self.turn += 1
                  if self.turn >= len(self.connections):
                    self.turn = 0

                  # Broadcast new state
                  await self.broadcast_state()

                  # is_turn_over
                  if self.game_state == GameState.DEALER:
                    await self.dealer_turn()
                  
                  return

                # Broadcast new state
                await self.broadcast_state()

                # Send available actions
                await self.websocket.send_json({"turn": self.connections[websocket], "actions": ["hit", "stand"]})
              case "stand":
                self.players_state[websocket] = PlayerState.STANDING

                if self.is_turn_over:
                  self.game_state = GameState.DEALER

                self.turn += 1
                if self.turn >= len(self.connections):
                  self.turn = 0

                # Broadcast new state
                await self.broadcast_state()

                if self.game_state == GameState.DEALER:
                  await self.dealer_turn()

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