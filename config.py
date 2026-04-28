import os
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()

# Получаем данные
BOT_TOKEN = os.getenv('TG_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
SHEET_ID = os.getenv('SHEET_ID')
DONATE_LINK = os.getenv('DONATE_LINK')
CREDS_FILE = 'credentials.json'

# Проверка на случай, если что-то забыли добавить в .env
if not BOT_TOKEN or not SHEET_ID:
    raise ValueError("❌ Ошибка: Проверь файл .env. Не хватает TG_TOKEN или SHEET_ID")