from fastapi import APIRouter, WebSocket, WebSocketDisconnect, BackgroundTasks, Query, Depends
from sqlalchemy.orm import Session
from ..auth import get_current_user
from ..db import get_db
import time

from .ws.chat import ChatManager
from .ws.blackjack import BlackjackManager
from ..blackjack.engine import Engine

# See: https://fastapi.tiangolo.com/tutorial/bigger-applications/
#      https://fastapi.tiangolo.com/advanced/websockets/

router = APIRouter(
  prefix="/ws",
  tags=["websockets"],
  dependencies=[],
  responses={404: {"description": "Not found"}},
)

chat_manager = ChatManager()
blackjack_manager = BlackjackManager()

@router.websocket("/chat/{room_id}")
async def chat_endpoint(websocket: WebSocket, room_id: str, access_token: str = Query(...), db: Session = Depends(get_db)):
  # try:
  #   username = (get_current_user(access_token, db)).username
  # except Exception as e:
  #   print(f"ERROR (WS chat): {e}", file=sys.stderr)
  #   return
  username = access_token

  room = await chat_manager.connect(room_id, websocket)
  try:
    while True:
      data = await websocket.receive_json(mode="text")
      
      if data == {}:
        continue

      print(data)

      # if sync then sync

      await room.broadcast({"time": time.time(), "username": username, "message": data["message"]}, save=True)
  except WebSocketDisconnect:
    chat_manager.disconnect(room_id, websocket)
    await room.broadcast({"time": time.time(), "username":username, "msg": "left the chat", "disconnected": True}, save=False)

@router.websocket("/blackjack/{room_id}")
async def blackjack_endpoint(websocket: WebSocket, room_id: str, access_token: str = Query(...), db: Session = Depends(get_db)):
  # try:
  #   username = (get_current_user(access_token, db)).username
  # except Exception as e:
  #   print(f"ERROR (WS Blackjack): {e}", file=sys.stderr)
  #   return

  username = access_token

  engine = await blackjack_manager.connect(room_id, websocket, username)
  try:
    while True:
      data = await websocket.receive_json(mode="text")
      
      if data == {}:
        continue

      await engine.feed(websocket, data)
  except WebSocketDisconnect:
    blackjack_manager.disconnect(room_id, websocket)
  
# TODO FOR TESTING PURPOSES ONLY

# async def start(room_id):
#   room = blackjack_manager.rooms[room_id]
#   room.start()
#   await room.run()
#   # try:
#   # except WebSocketDisconnect as e:
#   #   print(f"ERROR: {e}")
#   #   print("START FUNC SOCKET DISCONNECTED")
#   # except Exception:
#   #   print("DAFUCK")

# @router.get("/bj/start/{room_id}")
# async def start_blackjack(room_id: str, background_tasks: BackgroundTasks):
#   background_tasks.add_task(start, room_id)
#   return {"status": "ok"}

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
