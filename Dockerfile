FROM python:3.8.3-slim-buster

ENV DBSERVER="localhost"
ENV DBPORT=5432
ENV DATABASE="postgres"
ENV DBUSER="postgres"
ENV DB_PASSWORD_PATH="/run/secrets/db_password"
ENV APIUSER="admin"
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