from config import token
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from api import search_mangas

# Commands


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hello, World!")


# Response


async def handle_response(text: str) -> dict:
    mangas = await search_mangas(text)
    return mangas


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text: str = update.message.text
    buttons = await handle_response(text)
    await update.message.reply_text(f"Here are the mangas I found: {buttons.keys()}")


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("An error occurred")
    print(f"An error occurred: {context.error} caused by {update}")


if __name__ == "__main__":
    print("Bot is starting")
    app = Application.builder().token(token).build()

    # Commands
    app.add_handler(CommandHandler("start", start))

    # Response
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    app.add_error_handler(error)

    print("Bot is running")
    app.run_polling(poll_interval=3)
