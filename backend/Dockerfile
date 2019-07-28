FROM python:3.6-alpine

RUN apk update && apk upgrade && apk add bash
RUN pip install --upgrade pip

WORKDIR /app/backend/

COPY . .

RUN pip install -r requirements.txt

ENV MUSICRACY_BACKEND_NAME spotify
ENV PYTHONPATH $PYTHONPATH:/app/
ENV BACKEND_HOSTNAME 0.0.0.0
ENV BACKEND_PORT 5001


CMD ["python", "main.py"]
