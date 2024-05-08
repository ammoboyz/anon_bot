FROM ubuntu:latest
FROM python:3.10

RUN apt update
RUN apt install python3-pip -y

WORKDIR /usr/app/src

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN apt-get update
COPY . .