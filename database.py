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
            print("❌ Ошибка: Переменная GOOGLE_CREDS_JSON не найдена!")
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
                    rating_val = row[3].strip() # Убираем пробелы
                    
                    # Пробуем превратить в число. 
                    # Сначала в float (чтобы поймать 5.0), потом в int
                    if rating_val:
                        rating = int(float(rating_val))
                    else:
                        rating = 0
                    
                    songs.append({
                        'id': row[0],
                        'title': row[1],
                        'filename': row[2],
                        'rating': rating,
                        'file_id': row[5] # <-- File_ID из столбца F
                    })
                except Exception as e:
                    # Если не получилось преобразовать рейтинг, ставим 0
                    print(f"⚠️ Ошибка конвертации рейтинга для '{row[1]}': {e}")
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
            # key=lambda x: x['rating'] говорит: "сортируй по полю rating"
            # reverse=True говорит: "от большего к меньшему"
            songs.sort(key=lambda x: x['rating'], reverse=True)
            print(f"📊 Отсортированный топ: {[s['title'] + '(' + str(s['rating']) + ')' for s in songs[:3]]}")
            
        return songs
        
    except Exception as e:
        print(f"❌ Критическая ошибка в get_catalog: {e}")
        return []

def update_rating(song_id):
    """Увеличивает рейтинг песни на 1"""
    sheet = get_sheet('Catalog')
    if not sheet: return
    
    # Ищем строку с нужным ID песни (в первом столбце)
    try:
        cell = sheet.find(str(song_id), in_column=1)
        if cell:
            row_index = cell.row
            # Текущий рейтинг находится в 5-м столбце (E)
            current_rating = int(sheet.cell(row_index, 5).value or 0)
            new_rating = current_rating + 1
            sheet.update_cell(row_index, 5, new_rating)
            print(f"👍 Рейтинг песни {song_id} увеличен до {new_rating}")
    except Exception as e:
        print(f"Ошибка обновления рейтинга: {e}")

import telebot # Убедись, что импортирован, если нужно
# Но лучше передать объект bot из handlers

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
