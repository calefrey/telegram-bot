# syntax=docker/dockerfile:1
FROM python:3.7
WORKDIR /app
RUN pip3 install python-telegram-bot
COPY . .
CMD ["python3", "bot.py"]