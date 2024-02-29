from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.orm import Session
from ..auth import get_current_user
from ..db import get_db
from collections import deque
import time

# See: https://fastapi.tiangolo.com/tutorial/bigger-applications/
#      https://fastapi.tiangolo.com/advanced/websockets/

router = APIRouter(
  prefix="/ws",
  tags=["websockets"],
  dependencies=[],
  responses={404: {"description": "Not found"}},
)

class Room:
  def __init__(self, message_buffer_size: int | None = None):
    """ Websocket room with a message buffer.

    Args:
        message_buffer_size (int | None, optional): Length of the FIFO buffer that will store the n-th latest messages. Defaults to None.
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

class RoomManager:
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


chat_manager = RoomManager()

@router.websocket("/chat/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, access_token: str = Query(...), db: Session = Depends(get_db)):
  room = await chat_manager.connect(room_id, websocket)
  username = (await get_current_user(access_token, db)).username
  try:
    while True:
      data = await websocket.receive_json(mode="text")
      
      if data == {}:
        continue

      print(data)

      # if sync then sync

      await room.broadcast({"time": time.time(), "username":username, "msg": data["message"]}, save=True)
  except WebSocketDisconnect:
    chat_manager.disconnect(room_id, websocket)
    await room.broadcast({"time": time.time(), "username":username, "msg": "left the chat", "disconnected": True}, save=False)


# TODO FOR TESTING PURPOSES ONLY
html = """
<!DOCTYPE html>
<html>
<head> <title>Chat</title> </head>
<body>
  <h1>WebSocket Chat</h1>
  <p>Very quick and very dirty proof of concept</p>
  <h2>Token:  <textarea id="access_token" rows="3" cols="50"></textarea>
  <button id="btn_conectar">Conectarse</button>
  </h2>
  <h3>Chat:</h3>
  <form action="" onsubmit="sendMessage(event)">
    <input type="text" id="messageText" autocomplete="off" />
    <button id="btn_send">Send</button>
  </form>

  <ul id='messages'></ul>

  <script> // Imagine writing vanilla JS in 2024 LMAO
    const room_id = "__ROOMID__"

    let ws = null;
    
    const btn_conectar = document.getElementById('btn_conectar');
    const access_token = document.getElementById('access_token');
    const messages = document.getElementById('messages');
    const input = document.getElementById('messageText');
    const send = document.querySelector('btn_send');
    
    btn_conectar.disabled = true;
    btn_send.disabled = true;

    access_token.addEventListener('input', (e) => {
      if (e.target.value.length > 0) {
        btn_conectar.disabled = false;
      } else {
        btn_conectar.disabled = true;
      }
    });

    btn_conectar.addEventListener('click', (_) => { connect(); });
    
    const connect = () => {
      ws = new WebSocket(`ws://localhost:8000/ws/chat/${room_id}?access_token=${access_token.value}`);
    
      btn_send.disabled = false;
    
      ws.onmessage = (event) => {
        var message = document.createElement('li')
        var content = document.createTextNode(event.data)
        console.log(content)
        message.appendChild(content)
        messages.appendChild(message)
      };
    };

    const sendMessage = (event) => {
      event.preventDefault()
      if (!ws) return;
      if (input.value.length === 0) return;

      ws.send(JSON.stringify({ message: input.value, time: Date.now() }))
      input.value = ''
    };
  </script>
</body>
</html>
"""

from fastapi.responses import HTMLResponse
@router.get("/ui/chat/{room_id}")
async def get(room_id: str):
  rhtml = html.replace("__ROOMID__", room_id)
  return HTMLResponse(rhtml)
