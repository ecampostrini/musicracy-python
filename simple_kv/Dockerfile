FROM python:3.6-alpine

RUN apk update && apk upgrade && apk add bash

WORKDIR /app/simple_kv

COPY . .

RUN pip install --upgrade pip

ENV PYTHONPATH $PYTHONPATH:/app/
ENV SIMPLE_KV_HOST 0.0.0.0
ENV SIMPLE_KV_PORT 5002

CMD ["python", "main.py"]