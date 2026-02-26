import os
from dotenv import find_dotenv, load_dotenv

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

BOT_TOKEN: str = os.getenv("BOT_TOKEN")
AI_KEY: str = os.getenv("AI_KEY")
