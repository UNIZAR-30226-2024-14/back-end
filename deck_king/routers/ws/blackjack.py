from ...blackjack import Blackjack
from .wsplayer import WSPlayer

class BlackjackManager:
  def __init__(self):
    self.rooms: dict[str, Blackjack] = {}

  async def connect(self, key: str, player: WSPlayer) -> None:
    if key not in self.rooms:
      print(f"Creating new Blackjack room#{key}")
      self.rooms[key] = Blackjack([])
    
    await player.websocket.accept()
    self.rooms[key].add_player(player)
  
  def playing(self, key: str, player: WSPlayer) -> bool:
    if key in self.rooms:
      return player in self.rooms[key].players
    return False

  def disconnect(self, key: str, player: WSPlayer) -> None:
    if key in self.rooms:
      self.rooms[key].remove_player(player)

      # Small GC
      if len(self.rooms[key].players) == 0:
        print(f"Room#{key} is empty, deleting it")
        del self.rooms[key]