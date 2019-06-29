FROM python:3.6-alpine

RUN apk update && apk upgrade && apk add bash

WORKDIR /app/backend/

COPY . .

ENV MUSICRACY_BACKEND_NAME spotify
ENV PYTHONPATH $PYTHONPATH:/app/
ENV BACKEND_HOSTNAME 0.0.0.0
ENV BACKEND_PORT 5001

RUN pip install -r requirements.txt

CMD ["python", "/app/backend/main.py"]
