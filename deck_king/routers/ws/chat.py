from fastapi import WebSocket
from .room import Room

class ChatManager:
  def __init__(self):
    self.rooms: dict[str, Room] = {}
  
  async def connect(self, key: str, websocket: WebSocket, message_buffer_size: int | None = None) -> Room:
    if key not in self.rooms:
      print(f"Creating new room#{key}")
      self.rooms[key] = Room(message_buffer_size)
    
    await self.rooms[key].connect(websocket)
    return self.rooms[key]

  def disconnect(self, key: str, websocket: WebSocket):
    if key in self.rooms:
      self.rooms[key].disconnect(websocket)

      # Small GC
      if len(self.rooms[key]) == 0:
        print(f"Room#{key} is empty, deleting it")
        del self.rooms[key]