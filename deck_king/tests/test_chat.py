from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
import pytest

from ..main import app, clean_database

from .utils import register, login

# https://fastapi.tiangolo.com/advanced/testing-websockets/

client = TestClient(app)

def setup_function():
  clean_database()

def test_chat():
  username = "user_test"
  room_id = 123

  response = register(client, username, "test@test.com", "test")
  access_token = response.json()["access_token"]

  username = access_token # TODO: change

  with client.websocket_connect(f"/ws/chat/{room_id}?access_token={access_token}") as websocket:
    websocket.send_json(
      {"message": "Hello, world!"}
    )
    
    response = websocket.receive_json()

    assert "time" in response
    assert "username" in response
    assert "message" in response

    assert response["username"] == username
    assert response["message"] == "Hello, world!"
