FROM python:3.10.13-slim

LABEL Author="Javier Sancho Olano <815520@unizar.es>"

# set work directory
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY ./deck_king ./deck_king

EXPOSE 8000

# Start the app
CMD [ "uvicorn", "deck_king.main:app", "--host", "0.0.0.0" ]