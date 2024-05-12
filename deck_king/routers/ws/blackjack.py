from ...blackjack.engine import Engine
from fastapi import WebSocket

class BlackjackManager:
  def __init__(self):
    self.rooms: dict[str, Engine] = {}

  async def connect(self, key: str, player: WebSocket, username: str) -> Engine:
    if key not in self.rooms:
      print(f"Creating new Blackjack room#{key}")
      self.rooms[key] = Engine()
    
    await self.rooms[key].connect(player, username)
    return self.rooms[key]
  
  def disconnect(self, key: str, player: WebSocket) -> None:
    if key in self.rooms:
      self.rooms[key].disconnect(player)

      # Skip GC if room is paused
      if self.rooms[key].paused:
        return

      # Small GC
      if len(self.rooms[key].connections) == 0:
        print(f"Blackjack room#{key} is empty, deleting it")
        del self.rooms[key]
