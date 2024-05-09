def register(client, username, email, password):
  return client.post("/users/register",
                     json={"username": username, 
                           "email": email,
                           "password": password})

def login(client, username, password):
  return client.post("/users/token", 
                     data={"username": username, 
                           "password": password})
