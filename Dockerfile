FROM python:3.11

# Install Go
RUN apt update && apt install -y golang supervisor

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["supervisord", "-c", "/app/supervisord.conf"]
