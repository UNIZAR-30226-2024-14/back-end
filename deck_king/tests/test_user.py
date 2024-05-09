from fastapi.testclient import TestClient

from ..main import app, clean_database

from .utils import register, login

# https://fastapi.tiangolo.com/tutorial/testing/

client = TestClient(app)

def setup_function():
  clean_database()

def test_register_user():
  response = register(client, "test", "test@test.com", "test")
  assert response.status_code == 200
  assert "access_token" in response.json()

def test_login():
  rresponse = register(client, "test", "test@test.com", "test")
  lresponse = login(client, "test", "test")
  assert rresponse.status_code == 200
  assert lresponse.status_code == 200

def test_login_invalid():
  rresponse = register(client, "test", "test@test.com", "test")
  luresponse = login(client, "txest", "test")
  lpresponse = login(client, "test", "tsar23est")
   
  assert rresponse.status_code == 200
  assert luresponse.status_code == 401
  assert lpresponse.status_code == 401


def test_register_user_bad_email():
  bad_emails = ["test", "test@", "test.com", "test@test", "test@test.", 
                "test.test.c", "test&test.com", "test@test&com"]

  responses_status = []
  responses_json = []
  for email in bad_emails:
    response = register(client, "test", email, "test")
    responses_status.append(response.status_code == 400)
    responses_json.append(response.json() == {"detail": "Invalid email"})

  assert all(responses_status)
  assert all(responses_json)

def test_register_user_username_exists():
  register(client, "test", "test@test.com", "test")
  response = register(client, "test", "test2@test.com", "test")
  
  assert response.status_code == 400
  assert response.json() == {"detail": "Username already exists"}


def test_register_user_email_exists():
  register(client, "test", "test@test.com", "test")
  response = register(client, "test2", "test@test.com", "password") 

  assert response.status_code == 400
  assert response.json() == {"detail": "Email already exists"}
