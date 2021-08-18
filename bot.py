from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import logging, os, time

from ftplib import FTP

token = os.environ.get("TELEGRAM_TOKEN")
version = "1.2"
starttime = time.strftime("%m/%d/%Y, %H:%M:%S")
num_processed = 0

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

welcome_message = [
    "Welcome to the Alpha Vet Care Telegram Bot!",
    "To Upload a photo to the Impromed Server, touch the paperclip below, and select a photo.",
    "If you add a caption to the photo it will be uses as the filename.",
    "You can even upload multiple photos at once",
]

about_message = [
    "Helllo, I am the AVC Telegram Bot!",
    "you can send me a photo and I'll upload it to the Impromed Server.",
    "To start messaging me, tap my profile (the paw print) and tap the message buttom.",
    "Also, FYI: I can only read messages that start with a /",
]


def start(update, context):
    logger.info("Bot Started")
    update.message.reply_text("\n".join(welcome_message))


def about(update, context):
    chat = update.message.chat
    logger.info(
        f"{update.message.from_user.username} requested the About message in {chat.title or chat.username}"
    )
    update.message.reply_text("\n".join(about_message))
    pass


def debug(update, context):
    global num_processed
    update.message.reply_text(
        f"""
AVC Telegram Bot, version {version}
Started: {starttime}
Number of pictures processed: {num_processed}"""
    )


def upload(update, context):
    global num_processed
    num_processed += 1

    def save_photo(photo_id, filename):
        # save the photo to the bot server
        update.message.reply_text("Uploading...")
        context.bot.get_file(photo_id).download(filename)
        with open(filename, "rb") as f:
            try:
                with FTP("PDC1.clinic.vet") as ftp:
                    ftp.login()
                    ftp.storbinary("STOR " + filename, f)
                update.message.reply_text(f"Uploaded as {filename}")
            except Exception as e:
                logger.error(e)
                update.message.reply_text("Failed to upload.")
                update.message.reply_text("Please send the message below to Caleb:")
                update.message.reply_text(str(e))

        # delete the file from th bot server so it doesn't take up space
        if os.path.exists(filename):
            os.remove(filename)

    # saves the rest of the message as a string to be used as a filename
    user = update.message.from_user
    photo = update.message.photo
    photo_id = photo[-1].file_id
    media_group_id = update.message.media_group_id
    logger.info(f"Media group id is {media_group_id}")
    old_group_id = context.user_data.get("media_group_id", "0")  # defaults to 0

    # first photo in album
    if (
        update.message.media_group_id != old_group_id
        or update.message.media_group_id is None
    ):
        logger.info(f"Photo received from {user.first_name} {user.last_name}")
        user_initials = f"{user.first_name[0]}{user.last_name[0]}"
        context.user_data["photo_index"] = 1
        # record the media group id, which is needed to determine if subsequent photos are in the same album
        context.user_data["media_group_id"] = update.message.media_group_id

        # get caption or make one up
        caption = update.message.caption
        if not caption:  # caption specified
            caption = user_initials + time.strftime("-%Y%m%d-%H%M%S")
        context.user_data["caption"] = caption  # save the caption for later

        filename = caption + ".png"

    else:  # if the media group id is the same as the previous message, it's the same album
        logger.info(f"Photo from photo album recieved")
        # increment the photo index for saving the filename
        context.user_data["photo_index"] += 1
        filename = (
            context.user_data["caption"] + f"-{context.user_data['photo_index']}.png"
        )

    save_photo(photo_id, filename)


def error(update, context):
    logger.warning(f'Update "{update}" caused error "{context.error}"')


def main():
    # Initialize the bot
    updater = Updater(token=token, use_context=True)

    # Get the update dispatcher
    dp = updater.dispatcher

    # Define command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("about", about))
    dp.add_handler(CommandHandler("debug", debug))

    dp.add_handler(MessageHandler(Filters.photo, upload))

    # Define message handlers

    # Log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
