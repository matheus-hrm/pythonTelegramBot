import os
from typing import Final
from dotenv import load_dotenv

load_dotenv(override=True)

token: Final = os.getenv("TOKEN")
bot_username: Final = os.getenv("BOT_USERNAME")
