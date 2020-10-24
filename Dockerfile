FROM python:3.9-alpine

ENV PYTHONUNBUFFERED 1

COPY ./req.txt /req.txt
RUN pip install -r /req.txt

RUN mkdir /app
WORKDIR /app
COPY ./app /app

RUN adduser -D user
USER user
