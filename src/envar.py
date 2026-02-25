import os
from dotenv import find_dotenv, load_dotenv

dotenc_path = find_dotenv()
load_dotenv(dotenc_path)

BOT_TOKEN = os.getenv("BOT_TOKEN")
