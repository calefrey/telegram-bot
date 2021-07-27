A telegram bot that will automatically upload photos you send it to a server somewhere, using the caption as the filename.

This is being used to upload photos to an SMB share on the Alpha Vet Care Impromed Server.

Requirements:
* Telegram Bot API key
* Docker

To run, you'll need to build the dockerfile and specify the token as an environment variable.
```
docker build -t telegram-bot .
docker run -e TELEGRAM_TOKEN=<your telegram api key> telegram-bot
```