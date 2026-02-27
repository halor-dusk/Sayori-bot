from os import getenv
from dotenv import find_dotenv, load_dotenv

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

BOT_TOKEN: str = getenv("BOT_TOKEN")
GEMINY_KEY: str = getenv("GEMINY_KEY")
AI_KEY: str = getenv("AI_KEY")
