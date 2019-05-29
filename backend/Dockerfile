FROM python:3.6-alpine

RUN apk update && apk upgrade && apk add bash

COPY . /app/backend/

ENV MUSICRACY_BACKEND_NAME=spotify
ENV PYTHONPATH="$PYTHONPATH:/app/"

EXPOSE 9001

CMD ["python", "/app/backend/main.py"]
