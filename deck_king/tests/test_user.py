from fastapi.testclient import TestClient

from ..main import app, clean_database

client = TestClient(app)

def setup_function():
  clean_database()

def test_register_user():
  response = client.post("/users/register",
                         json={"username": "test", 
                               "email": "test@test.com",
                               "password": "test"})
  assert response.status_code == 200
  assert "access_token" in response.json()

def test_login():
  rresponse = client.post("/users/register",
                          json={"username": "test", 
                                "email": "test@test.com",
                                "password": "test"})

  lresponse = client.post("/users/token", 
                          data={"username": "test", 
                                "password": "test"})
  
  assert rresponse.status_code == 200
  assert lresponse.status_code == 200
  assert rresponse.json() == lresponse.json()
  

def test_register_user_bad_email():
  bad_emails = ["test", "test@", "test.com", "test@test", "test@test.", 
                "test.test.c", "test&test.com", "test@test&com"]


  responses_status = []
  responses_json = []
  for email in bad_emails:
    response = client.post("/users/register",
                          json={"username": "test", 
                                "email": email,
                                "password": "test"})
    responses_status.append(response.status_code == 400)
    responses_json.append(response.json() == {"detail": "Invalid email"})

  assert all(responses_status)
  assert all(responses_json)

def test_register_user_username_exists():
  client.post("/users/register",
              json={"username": "test", 
                    "email": "test@test.com",
                    "password": "test"})

  response = client.post("/users/register",
                         json={"username": "test", 
                               "email": "test2@test.com",
                               "password": "test"})
  
  assert response.status_code == 400
  assert response.json() == {"detail": "Username already exists"}


def test_register_user_email_exists():
  client.post("/users/register",
              json={"username": "test", 
                    "email": "test@test.com",
                    "password": "test"})

  response = client.post("/users/register",
                         json={"username": "test2", 
                               "email": "test@test.com",
                               "password": "test"})
  
  assert response.status_code == 400
  assert response.json() == {"detail": "Email already exists"}