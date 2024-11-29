from callbacks import CallbackTypes
from config import token
from api import get_chapter_pages, get_manga_chapters, search_mangas
from telegram import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Update,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith(CallbackTypes.MANGA.value):
        manga_id = data.replace(CallbackTypes.MANGA.value, "")
        await handle_chapter_selection(query, context, manga_id)

    elif data.startswith(CallbackTypes.LANGUAGE.value):
        await handle_language_selection(query, context)

    elif data.startswith(CallbackTypes.CHAPTER.value):
        chapter_id = data.replace(CallbackTypes.CHAPTER.value, "")
        await handle_page_selection(query, context, chapter_id)

    elif data.startswith(CallbackTypes.PAGE.value):
        await handle_page_navigation(query, context)

    elif data.startswith(CallbackTypes.NAVIGATION.value):
        await handle_chapter_list_navigation(query, context)

    elif data.startswith(CallbackTypes.QUALITY.value):
        await handle_quality_selection(query, context)
    else:
        await query.edit_message_text(f"Callback data: {data}")


async def handle_chapter_selection(
    query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, manga_id: str
) -> None:
    language = "en"
    if context.user_data.get("lang"):
        language = context.user_data.get("lang")
    chapters = await get_manga_chapters(manga_id, language)
    context.user_data["current_manga_id"] = manga_id

    chapter_buttons = [
        [
            InlineKeyboardButton(
                key, callback_data=f"{CallbackTypes.CHAPTER.value}{value}"
            )
        ]
        for key, value in chapters.items()
    ]
    nav_buttons = [
        [
            InlineKeyboardButton(
                "⏪", callback_data=f"{CallbackTypes.NAVIGATION.value}first"
            ),
            InlineKeyboardButton(
                "⬅️", callback_data=f"{CallbackTypes.NAVIGATION.value}prev"
            ),
            InlineKeyboardButton(
                "➡️", callback_data=f"{CallbackTypes.NAVIGATION.value}next"
            ),
            InlineKeyboardButton(
                "⏩", callback_data=f"{CallbackTypes.NAVIGATION.value}last"
            ),
        ]
    ]
    buttons = chapter_buttons + nav_buttons
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.edit_message_reply_markup(reply_markup)


async def handle_chapter_list_navigation(
    query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE
) -> None:
    manga_id = context.user_data.get("current_manga_id")
    offset = context.user_data.get("chapter_offset", 0)
    language = context.user_data.get("lang", "en")
    data = query.data.replace(CallbackTypes.NAVIGATION.value, "")

    if data == "first":
        offset = 0
    elif data == "prev":
        offset = max(0, offset - 10)
    elif data == "next":
        offset = offset + 10
    elif data == "last":
        offset = 100

    context.user_data["chapter_offset"] = offset
    print(offset, language, manga_id)
    try:
        chapters = await get_manga_chapters(manga_id, language, offset)

        chapter_buttons = [
            [
                InlineKeyboardButton(
                    key, callback_data=f"{CallbackTypes.CHAPTER.value}{value}"
                )
            ]
            for key, value in chapters.items()
        ]
        nav_buttons = [
            [
                InlineKeyboardButton(
                    "⏪", callback_data=f"{CallbackTypes.NAVIGATION.value}first"
                ),
                InlineKeyboardButton(
                    "⬅️", callback_data=f"{CallbackTypes.NAVIGATION.value}prev"
                ),
                InlineKeyboardButton(
                    "➡️", callback_data=f"{CallbackTypes.NAVIGATION.value}next"
                ),
                InlineKeyboardButton(
                    "⏩", callback_data=f"{CallbackTypes.NAVIGATION.value}last"
                ),
            ]
        ]
        buttons = chapter_buttons + nav_buttons
        reply_markup = InlineKeyboardMarkup(buttons)

        await query.edit_message_reply_markup(reply_markup)
        await query.answer(f"Page {(offset//10)+1}")
    except Exception as e:
        print(f"Error getting chapters: {e}")
        await query.edit_message_text("Error getting chapters")


async def handle_language_selection(
    query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE
) -> None:
    language = query.data.replace(CallbackTypes.LANGUAGE.value, "")
    context.user_data["lang"] = language
    await query.edit_message_text(f"Language changed to {language}")


async def handle_page_selection(
    query: CallbackQuery,
    context: ContextTypes.DEFAULT_TYPE,
    chapter_id: str,
) -> None:
    quality = context.user_data.get("quality", True)
    pages = await get_chapter_pages(chapter_id, quality)
    if not pages:
        await query.edit_message_text(
            "Chapter not found, try changing the language source"
        )
        return

    media = InputMediaPhoto(media=pages[0])
    await query.edit_message_media(media=media)

    context.user_data["pages"] = pages
    context.user_data["page"] = 0
    context.user_data["chapter_pages"] = len(pages)

    buttons = [
        [
            InlineKeyboardButton(
                "⏪", callback_data=f"{CallbackTypes.PAGE.value}first"
            ),
            InlineKeyboardButton("⬅️", callback_data=f"{CallbackTypes.PAGE.value}prev"),
            InlineKeyboardButton("➡️", callback_data=f"{CallbackTypes.PAGE.value}next"),
            InlineKeyboardButton("⏩", callback_data=f"{CallbackTypes.PAGE.value}last"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.edit_message_reply_markup(reply_markup)


async def handle_page_navigation(
    query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE
) -> None:
    page = context.user_data.get("page", 0)
    pages = context.user_data.get("pages", [])
    chapter_pages = context.user_data.get("chapter_pages", 0)
    data = query.data.replace(CallbackTypes.PAGE.value, "")

    if not pages or chapter_pages == 0:
        await query.edit_message_text("No pages found")
        return

    if data == "first":
        page = 0
    elif data == "prev":
        page = max(0, page - 1)
    elif data == "next":
        page = min(chapter_pages - 1, page + 1)
    elif data == "last":
        page = chapter_pages - 1

    context.user_data["page"] = page
    media = InputMediaPhoto(media=pages[page])

    if page < 0:
        page = 0
    elif page >= chapter_pages:
        page = chapter_pages - 1

    await query.edit_message_media(
        media=media,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⏪", callback_data=f"{CallbackTypes.PAGE.value}first"
                    ),
                    InlineKeyboardButton(
                        "⬅️", callback_data=f"{CallbackTypes.PAGE.value}prev"
                    ),
                    InlineKeyboardButton(
                        "➡️", callback_data=f"{CallbackTypes.PAGE.value}next"
                    ),
                    InlineKeyboardButton(
                        "⏩", callback_data=f"{CallbackTypes.PAGE.value}last"
                    ),
                ]
            ]
        ),
    )
    await query.answer(f"Page {page + 1}/{chapter_pages}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hello, use the /search command to search for mangas"
    )


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(update.message.text.split(" ", 1)) == 1:
        await update.message.reply_text("Please enter a manga name to search:")
        return

    text = update.message.text.split(" ", 1)[1]
    data = await search_mangas(text)

    buttons = [
        [InlineKeyboardButton(name, callback_data=f"{CallbackTypes.MANGA.value}{id}")]
        for name, id in data.items()
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(
        "Here are the mangas I found:", reply_markup=reply_markup
    )


async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [
            InlineKeyboardButton(
                "English", callback_data=f"{CallbackTypes.LANGUAGE.value}en"
            ),
            InlineKeyboardButton(
                "Spanish", callback_data=f"{CallbackTypes.LANGUAGE.value}es"
            ),
            InlineKeyboardButton(
                "Portuguese", callback_data=f"{CallbackTypes.LANGUAGE.value}pt-br"
            ),
            InlineKeyboardButton(
                "French", callback_data=f"{CallbackTypes.LANGUAGE.value}fr"
            ),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Please choose a language:", reply_markup=reply_markup
    )


async def change_quality(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [
            InlineKeyboardButton(
                "High Quality", callback_data=f"{CallbackTypes.QUALITY.value}data"
            ),
            InlineKeyboardButton(
                "Low Quality", callback_data=f"{CallbackTypes.QUALITY.value}dataSaver"
            ),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Please choose image quality:", reply_markup=reply_markup
    )


async def handle_quality_selection(
    query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE
) -> None:
    quality = query.data.replace(CallbackTypes.QUALITY.value, "")
    context.user_data["quality"] = quality
    await query.edit_message_text(f"Quality changed to {quality}")


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("An error occurred")
    print(f"An error occurred: {context.error} caused by {update}")


if __name__ == "__main__":
    print("Bot is starting")
    app = Application.builder().token(token).build()

    # Commands
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("language", change_language))
    app.add_handler(CommandHandler("quality", change_quality))

    # Callbacks
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_error_handler(error)

    print("Bot is running")
    app.run_polling(poll_interval=3)
