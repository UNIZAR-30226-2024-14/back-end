from dotenv import load_dotenv
from os import environ

load_dotenv()

# openssl rand -hex 32
JWT_SECRET_KEY = environ.get("JWT_SECRET_KEY")
JWT_ALGORITHM = environ.get("JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES"))

DB_USER = environ.get("DB_USER")
DB_PASSWORD = environ.get("DB_PASSWORD")
DB_HOST = environ.get("DB_HOST")
DB_PORT = int(environ.get("DB_PORT"))
DB_NAME = environ.get("DB_NAME")

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# SQLALCHEMY_DATABASE_URL = environ.get("SQLALCHEMY_DATABASE_URL")

