FROM python:3.8.3-slim-buster

ENV DB_SERVER="localhost"
ENV DB_PORT=5432
ENV DB_NAME="postgres"
ENV DB_USER="postgres"
ENV DB_PASSWORD_PATH="/run/secrets/db_password"
ENV API_USER="admin"
ENV API_PASSWORD_PATH="/run/secrets/api_password"

RUN apt update && apt install -y \
    libpq-dev \
    build-essential && \
    pip install \
    psycopg2 \
    flask \
    waitress

COPY ./app/ /opt/

EXPOSE 5000

ENTRYPOINT [ "python", "/opt/app.py" ]