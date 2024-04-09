from fastapi import WebSocket
from collections import deque

class Room:
  def __init__(self, message_buffer_size: int | None = None):
    """ Websocket room with a message buffer.

    Args:
        message_buffer_size (int | None, optional): Length of the FIFO buffer that will store the n-th latest messages. Defaults to None which means unlimited.
    """
    self.buffer = deque(maxlen=message_buffer_size)
    self.connections: list[WebSocket] = []
  
  @property
  def messages(self):
    return list(self.buffer)
  
  def __len__(self): # RENAME ?
    return len(self.connections)
  
  async def connect(self, websocket: WebSocket):
    """Connect a new websocket to the room.

    Args:
        websocket (WebSocket): Websocket to connect.
    """
    await websocket.accept()
    self.connections.append(websocket)

  def disconnect(self, websocket: WebSocket):
    """Disconnect a websocket from the room.

    Args:
        websocket (WebSocket): Websocket to disconnect.
    """
    self.connections.remove(websocket)
  
  async def broadcast(self, message: str | dict, save: bool = True):
    """Broadcast a message to all the websockets in the room.

    Args:
        message (str): Message to broadcast.
    """
    if save:
      self.buffer.append(message)

    for connection in self.connections:
      if isinstance(message, dict):
        await connection.send_json(message)
      else:
        await connection.send_text(message)
  
  async def send_to(self, to: WebSocket, message: str | dict, save: bool = True):
    """Send a message to a specific websocket in the room.

    Args:
        to (WebSocket): Websocket to send the message to.
        message (str): Message to send.
    """
    if save:
      self.buffer.append(message)

    if isinstance(message, dict):
      await to.send_json(message)
    else:
      await to.send_text(message)