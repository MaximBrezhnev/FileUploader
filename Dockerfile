FROM python:3.11
RUN apt-get update -y
RUN apt-get upgrade -y

WORKDIR /app
COPY . .

RUN fc-cache -f -v

RUN pip install -r requirements.txt