from fastapi import WebSocket, WebSocketDisconnect
from ...blackjack.player import Player, PlayerAction, PlayerState
from ...blackjack.deck import Card
import asyncio

class WSPlayer(Player):
  def __init__(self, websocket: WebSocket, username: str, on_socket_disconnect: callable):
    self.websocket = websocket
    self.username = username

    self.on_socket_disconnect = on_socket_disconnect

    self.lock = asyncio.Lock()

  async def on_update(self, help: str,
                      dealer_cards: list[Card],
                      states: dict[Player, PlayerState],
                      cards: dict[Player, list[Card]],
                      pot: dict[Player, int]) -> None:
    d_cards = [str(card) for card in dealer_cards]
    st = {player.username: str(state) for player, state in states.items()}
    cs = {player.username: [str(card) for card in cards[player]] for player in cards}
    p = {player.username: pot[player] for player in pot}

    try:
      await self.websocket.send_json({
        "help": help,
        "dealer_cards": d_cards,
        "states": st,
        "cards": cs,
        "pot": p
      })
    except WebSocketDisconnect:
      print(f"Player {self.username} disconnected")
      self.on_socket_disconnect(self)
      self.lock.release()

  async def on_turn(self, dealer_cards: list[Card], player_cards: list[Card], available_actions: list[PlayerAction]) -> PlayerAction:
    try:
      # Send info to player
      await self.websocket.send_json({
        "action": "turn",
        "your_best": sum(player_cards).best(),
        "available_actions": [str(action) for action in available_actions]
      })

      # Wait for action
      data = await self.websocket.receive_json()
      print(f"Got: {data}")

      return available_actions[int(data["action"])]
    except WebSocketDisconnect:
      print(f"Player {self.username} disconnected")
      self.lock.release()

  async def get_bet(self) -> int:
    try:
      print("Asking for bet!!")
      # ask for bet
      await self.websocket.send_json({"action": "bet"})
      # wait for bet
      print("Waiting for bet!!")
      data = await self.websocket.receive_json()
      print(f"Got: {data}")

      return int(data["bet"])
    except WebSocketDisconnect:
      print(f"Player {self.username} disconnected")
      self.lock.release()

  async def on_end(self) -> None:
    self.lock.release()

  async def wait_end(self) -> None:
    await self.lock.acquire()
    self.lock.release()

  def __hash__(self) -> int:
    return hash((self.websocket, self.username))

  def __eq__(self, other) -> bool:
    return isinstance(other, WSPlayer) and self.websocket == other.websocket and self.username == other.username

