import os
from dotenv import load_dotenv

# Загружаем переменные из файла .env (если он есть локально)
load_dotenv()

# Получаем данные из переменных окружения Render
# Если переменной нет, используем запасной вариант (для локального теста)
TG_TOKEN = os.getenv('TG_TOKEN') or '8680234949:AAHMsx6vSeKvWyiiWJjDIC77PtJ0o7H_Ctw'
ADMIN_ID = int(os.getenv('ADMIN_ID') or '1161773989')
SHEET_ID = os.getenv('SHEET_ID') or '1R4Y0AKwwmaXd_MXoyHmd7gycrfPiY6T9X_MOEW5mzPs'
DONATE_LINK = os.getenv('DONATE_LINK') or 'https://pay.cloudtips.ru/p/0a1a32b5'
CREDS_FILE = 'credentials.json'

# Проверка (опционально)
if not TG_TOKEN:
    raise ValueError("❌ Ошибка: Не задан TG_TOKEN")
