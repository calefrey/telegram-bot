FROM python:3.7-slim
WORKDIR /app
COPY . .
RUN pip3 install python-telegram-bot
CMD ["python3", "bot.py"]