from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
import pytest

from ..main import app, clean_database

# https://fastapi.tiangolo.com/advanced/testing-websockets/

client = TestClient(app)

def setup_function():
  clean_database()

@pytest.mark.skip(reason="Not implemented")
def test_create_table():
  pass

@pytest.mark.skip(reason="Not implemented")
def test_join_table():
  pass

@pytest.mark.skip(reason="Not implemented")
def test_search_table():
  pass

@pytest.mark.skip(reason="Not implemented")
def test_play_table():
  pass
