import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# Те же данные, что и в config.py
SHEET_ID = '1R4Y0AKwwmaXd_MXoyHmd7gycrfPiY6T9X_MOEW5mzPs'
CREDS_FILE = 'credentials.json'

def test_connection():
    print("🔄 Попытка подключения к Google...")
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
        client = gspread.authorize(creds)
        
        print("✅ Авторизация прошла успешно!")
        
        # Пробуем открыть лист Catalog
        sheet = client.open_by_key(SHEET_ID).worksheet("Catalog")
        print(f"✅ Лист 'Catalog' найден. Заголовки: {sheet.row_values(1)}")
        
        # Пробуем открыть лист Orders
        sheet_orders = client.open_by_key(SHEET_ID).worksheet("Orders")
        print(f"✅ Лист 'Orders' найден. Заголовки: {sheet_orders.row_values(1)}")
        
        # Пробуем записать тестовую строку
        print("📝 Пробую записать тестовую строку в Orders...")
        sheet_orders.append_row(["TEST", "TEST_ID", "NOW", "TEST_DETAILS", "New"])
        print("✅ ЗАПИСЬ УСПЕШНА! Проверь таблицу.")
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")

if __name__ == "__main__":
    test_connection()