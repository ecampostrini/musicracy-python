FROM python:3.6-alpine

RUN apk update && apk upgrade && apk add bash
RUN pip install --upgrade pip

WORKDIR /app/frontend/

COPY . .

RUN pip install -r requirements.txt

ENV PYTHONPATH $PYTHONPATH:/app/
ENV MUSICRACY_PROXY spotify
ENV BACKEND_HOST 0.0.0.0
ENV BACKEND_PORT 5001

# ENV FRONTEND_HOST 0.0.0.0
# ENV FRONTEND_PORT 5000
# ENV FLASK_APP main.py
# ENV FLASK_RUN_HOST 0.0.0.0
# ENV FLASK_RUN_PORT 5000

ENV FRONTEND_HOST 0.0.0.0
ENV FRONTEND_PORT 5000

# CMD ["python", "main.py"]
CMD gunicorn -b ${FRONTEND_HOST}:${FRONTEND_PORT} "main:getApp()"