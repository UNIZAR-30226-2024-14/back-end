#!/bin/bash

# Borrar versiones anteriores si existen
docker stop deck_king
docker rm deck_king

# Crear imagen
docker build -t deck_king_docker .

# Run!
docker run -d --name deck_king -p 8000:8000 deck_king_docker
