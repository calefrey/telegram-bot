from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
)
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
import logging, os, time

from ftplib import FTP

token = os.environ.get("TELEGRAM_TOKEN")
version = "1.3"
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
    "To send feedback, send the message /feedback",
]

about_message = [
    f"Helllo, I am the AVC Telegram Bot, v{version}.",
    "You can send me a photo and I'll upload it to the Impromed Server.",
    "I can also submit anonymous feedback to management as a virtual suggestion box."
    "To start messaging me, tap my profile (the paw print) and tap the message buttom.",
]


def start(update, context):
    logger.info("Bot Started")
    update.message.reply_text("\n".join(welcome_message))


def about(update, context):
    chat = update.message.chat
    logger.info(
        f"{update.message.from_user.username} requested the About message in {chat.title or chat.username}"
    )
    update.message.reply_text(
        "\n".join(about_message),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Source Code available on Github",
                        url="https://github.com/calefrey/telegram-bot",
                    )
                ]
            ]
        ),
    )
    pass


feedback_message = [
    "Your next message will be submitted, anonylmously, as feedback to management.",
    "You can treat it like a suggestions box, but without the ability to recognize handwriting.",
    "This bot does not record any of this information. It just passes it along.",
    "If you want to cancel, just type /cancel",
]
FEEDBACK = range(1)


def feedback(update, context):
    update.message.reply_text(
        "\n".join(feedback_message),
        reply_markup=ReplyKeyboardRemove(),
    )
    return FEEDBACK


def cancel(update, context):
    update.message.reply_text("Cancelled")
    return ConversationHandler.END


def submit_feedback(update, context):
    update.message.reply_text("Thanks for your feedback!")
    context.bot.send_message(chat_id="@avcfeedback", text=update.message.text)
    return ConversationHandler.END


def debug(update, context):
    global num_processed
    update.message.reply_text(
        f"AVC Telegram Bot, version {version}\n"
        + f"Started at {starttime}\n"
        + f"Processed {num_processed} pictures"
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
    dp.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("feedback", feedback)],
            states={
                FEEDBACK: [
                    MessageHandler(Filters.text & ~Filters.command, submit_feedback)
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )
    )

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
