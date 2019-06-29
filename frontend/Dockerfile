FROM python:3.6-alpine

RUN apk update && apk upgrade && apk add bash

WORKDIR /app/frontend/

COPY . .

ENV PYTHONPATH $PYTHONPATH:/app/
ENV MUSICRACY_PROXY spotify
ENV BACKEND_HOST 0.0.0.0
ENV BACKEND_PORT 5001
# ENV FRONTEND_HOST 0.0.0.0
# ENV FRONTEND_PORT 5000

ENV FLASK_APP app.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_RUN_PORT 5000

RUN pip install -r requirements.txt

CMD ["python", "/app/frontend/app.py"]