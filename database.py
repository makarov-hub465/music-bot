import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
from config import SHEET_ID
from datetime import datetime

def get_sheet(sheet_name):
    """Подключается к нужному листу таблицы используя переменную окружения"""
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        # Получаем JSON из переменной окружения
        creds_json = os.getenv('GOOGLE_CREDS_JSON_V2')
        
        if not creds_json:
            print("❌ Ошибка: Переменная GOOGLE_CREDS_JSON_V2 не найдена!")
            return None 
            
        # Преобразуем строку JSON в словарь
        creds_dict = json.loads(creds_json)
        
        # Создаем учетные данные из словаря
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        return sheet
    except Exception as e:
        print(f"❌ Ошибка подключения к таблице {sheet_name}: {e}")
        return None

def add_user(user_id, name):
    """Добавляет нового пользователя в лист Users, если его там нет"""
    sheet = get_sheet('Users')
    if not sheet: return
    
    # Проверяем, есть ли уже такой ID
    all_ids = sheet.col_values(1)
    if str(user_id) in all_ids:
        return # Пользователь уже есть
    
    # Добавляем новую строку
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([user_id, name, now])
    print(f"✅ Новый пользователь добавлен: {name}")

def get_catalog(sort_by_rating=False):
    """Возвращает список песен из таблицы Catalog"""
    try:
        sheet = get_sheet('Catalog')
        if not sheet:
            print("❌ Не удалось подключиться к листу Catalog")
            return []
            
        data = sheet.get_all_values()
        
        songs = []
        # Начинаем с 1, чтобы пропустить заголовок таблицы
        for row in data[1:]:
            # Проверяем, что в строке достаточно данных (минимум 6 колонок)
            if len(row) >= 6: 
                try:
                    # 1. Берем значение рейтинга из столбца E (индекс 4)
                    raw_rating = row[4] 
                    
                    # 2. Очищаем его от всего мусора
                    cleaned_rating = str(raw_rating).strip().replace(',', '.')
                    
                    # 3. Превращаем в число
                    if cleaned_rating:
                        rating = int(float(cleaned_rating))
                    else:
                        rating = 0
                    
                    songs.append({
                        'id': row[0],      # A
                        'title': row[1],   # B
                        'filename': row[2],# C
                        'rating': rating,  # E
                        'file_id': row[5]  # F
                    })
                except Exception as e:
                    print(f"⚠️ Ошибка конвертации для '{row[1]}': {e}")
                    # Если ошибка, добавляем с рейтингом 0, чтобы не терять песню
                    songs.append({
                        'id': row[0],
                        'title': row[1],
                        'filename': row[2],
                        'rating': 0,
                        'file_id': row[5]
                    })
            else:
                 print(f"⚠️ Пропущена короткая строка: {row}")
        
        if sort_by_rating:
            # Сортируем по рейтингу (по убыванию)
            songs.sort(key=lambda x: x['rating'], reverse=True)
            
        return songs
        
    except Exception as e:
        print(f"❌ Критическая ошибка в get_catalog: {e}")
        return []

def add_order(user_id, details, bot=None, admin_id=None):
    """Добавляет заявку и сообщает админу о результате"""
    try:
        sheet = get_sheet('Orders')
        
        if not sheet:
            if bot and admin_id:
                bot.send_message(admin_id, "❌ ОШИБКА: Лист 'Orders' не найден в таблице!")
            return
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        order_id = int(datetime.now().timestamp())
        
        # Пробуем записать
        sheet.append_row([order_id, user_id, now, details, "New"])
        
        # Сообщаем об успехе
        if bot and admin_id:
            bot.send_message(admin_id, f"✅ ЗАЯВКА ЗАПИСАНА!\nID: {order_id}\nТекст: {details}")
            
    except Exception as e:
        # Сообщаем об ошибке
        if bot and admin_id:
            bot.send_message(admin_id, f"❌ ОШИБКА ЗАПИСИ В ТАБЛИЦУ:\n{str(e)}")

def save_review(user_id, song_title, review_text):
    """Сохраняет отзыв в лист Reviews"""
    sheet = get_sheet('Reviews')
    if not sheet: return
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([now, user_id, song_title, review_text])

def vote_for_song(song_id):
    """Увеличивает рейтинг песни на 1 (используется в новом хендлере)"""
    try:
        sheet = get_sheet('Catalog')
        data = sheet.get_all_values()
        
        for i, row in enumerate(data[1:], start=2):
            if str(row[0]) == str(song_id):
                current_rating = int(row[4]) if row[4].isdigit() else 0
                new_rating = current_rating + 1
                cell_address = f"E{i}"
                sheet.update(cell_address, [[new_rating]])
                return True
        return False
    except Exception as e:
        print(f"Ошибка голосования: {e}")
        return False
