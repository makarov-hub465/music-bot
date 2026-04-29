import os
from dotenv import load_dotenv

load_dotenv()

# Используем имя BOT_TOKEN, как было изначально
BOT_TOKEN = os.getenv('TG_TOKEN') or '8680234949:AAHMsx6vSeKvWyiiWJjDIC77PtJ0o7H_Ctw'
ADMIN_ID = int(os.getenv('ADMIN_ID') or '1161773989')
SHEET_ID = os.getenv('SHEET_ID') or '1R4Y0AKwwmaXd_MXoyHmd7gycrfPiY6T9X_MOEW5mzPs'
DONATE_LINK = os.getenv('DONATE_LINK') or 'https://pay.cloudtips.ru/p/0a1a32b5'
CREDS_FILE = 'credentials.json'
