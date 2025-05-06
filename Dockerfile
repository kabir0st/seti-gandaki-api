FROM python:3.12.3-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt /app/

RUN apt update && apt install -y curl libpq-dev libcairo2 gcc postgresql-client gunicorn
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN pip install watchdog
COPY . /app/
RUN chmod +x /app/src/entrypoint.sh

EXPOSE 8989
WORKDIR /app/src

COPY src/.env.template src/.env

ENTRYPOINT ["/app/src/entrypoint.sh"]

CMD ["daphne", "-b", "0.0.0.0", "-p", "8989", "core.asgi:application"]