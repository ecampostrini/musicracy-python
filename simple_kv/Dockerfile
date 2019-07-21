FROM python:3.6-alpine

WORKDIR /app/simple_kv

COPY . .

ENV PYTHONPATH $PYTHONPATH:/app/
ENV SIMPLE_KV_HOST 0.0.0.0
ENV SIMPLE_KV_PORT 5002

CMD ["python", "/app/simple_kv/main.py"]