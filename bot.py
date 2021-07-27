from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from secret import token
import logging, os, time


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


def start(update, context):
    logger.info("Bot Started")
    update.message.reply_text("\n".join(welcome_message))


def upload(update, context):
    def save_photo(photo_id, filename) -> bool:
        # save the photo to the bot server
        context.bot.get_file(photo_id).download(filename)
        # Save to Impromed server
        #
        #
        #
        return True

    # saves the rest of the message as a string to be used as a filename
    user = update.message.from_user
    photo = update.message.photo
    photo_id = photo[-1].file_id
    media_group_id = update.message.media_group_id
    logger.info(f"Media group id is {media_group_id}")
    old_group_id = context.user_data.get("media_group_id", "0")  # defaults to 0

    # first photo in album
    if update.message.media_group_id != old_group_id:
        logger.info(f"Photo received from {user.first_name} {user.last_name}")
        context.user_data["photo_index"] = 1
        # record the media group id, which is needed to determine if subsequent photos are in the same album
        context.user_data["media_group_id"] = update.message.media_group_id

        # get caption or make one up
        caption = update.message.caption
        if not caption:  # caption specified
            caption = user.first_name + time.strftime("-%Y%m%d-%H%M")
        context.user_data["caption"] = caption  # save the caption for later

        filename = caption + ".png"

    else:  # if the media group id is the same as the previous message, it's the same album
        logger.info(f"Photo from photo album recieved")
        # increment the photo index for saving the filename
        context.user_data["photo_index"] += 1
        filename = (
            context.user_data["caption"] + f"-{context.user_data['photo_index']}.png"
        )

    update.message.reply_text(f"Uploading photo as {filename}...")
    success = save_photo(photo_id, filename)
    if success:
        update.message.reply_text("Uploaded!")
    else:
        update.message.reply_text("There was an error")

    # Download the best photo version

    ## Unwritten code to upload to the server
    #
    #
    #
    #

    # delete the photo from the bot server
    # if os.path.exists(filename):
    #     os.remove(filename)


def help(update, context):
    update.message.reply_text(
        "Send an image with a caption to upload to the impromed server"
    )


def error(update, context):
    logger.warning(f'Update "{update}" caused error "{context.error}"')


def main():
    # Initialize the bot
    updater = Updater(token=token, use_context=True)

    # Get the update dispatcher
    dp = updater.dispatcher

    # Define command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
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
