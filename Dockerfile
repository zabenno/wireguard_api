FROM python:3.8.3-slim-buster

ENV DBSERVER="localhost"
ENV DBPORT=5432
ENV DATABASE="postgres"
ENV DBUSER="postgres"
ENV DBPASSWORD="changeme123"

RUN apt update && apt install -y \
    libpq-dev \
    build-essential && \
    pip install \
    psycopg2 \
    flask \
    waitress

COPY ./app/ /opt/

ENTRYPOINT [ "python", "/opt/app.py" ]