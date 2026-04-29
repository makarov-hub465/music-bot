import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
from config import SHEET_ID

def get_sheet(sheet_name):
    """Подключается к нужному листу таблицы используя переменную окружения"""
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        # Получаем JSON из переменной окружения
        creds_json = os.getenv('GOOGLE_CREDS_JSON')
        
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
    """
    Возвращает список песен.
    Если sort_by_rating=True, сортирует по убыванию рейтинга (столбец E, индекс 4).
    """
    sheet = get_sheet('Catalog')
    if not sheet: return []
    
    rows = sheet.get_all_values()
    data = rows[1:] # Убираем заголовок
    
    if sort_by_rating:
        # Сортируем данные: key=lambda x: int(x[4]) берет 5-й столбец (Рейтинг)
        # reverse=True означает от большего к меньшему
        try:
            data.sort(key=lambda x: int(x[4]) if x[4].isdigit() else 0, reverse=True)
        except Exception as e:
            print(f"Ошибка сортировки: {e}")
            
    return data

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

def add_order(user_id, details):
    """Добавляет заявку на заказ в лист Orders"""
    print(f"🔍 Ищу лист 'Orders' для пользователя {user_id}...") # <--- МАЯЧОК 1
    
    sheet = get_sheet('Orders')
    
    if not sheet:
        print("❌ ОШИБКА: Лист 'Orders' не найден или нет доступа!") # <--- МАЯЧОК 2
        return
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    order_id = int(datetime.now().timestamp())
    
    try:
        print(f"📝 Пытаюсь записать строку: [{order_id}, {user_id}, {now}, ...]") # <--- МАЯЧОК 3
        sheet.append_row([order_id, user_id, now, details, "New"])
        print("✅ ЗАПИСЬ УСПЕШНА!") # <--- МАЯЧОК 4
    except Exception as e:
        print(f"❌ ОШИБКА ПРИ ЗАПИСИ В ТАБЛИЦУ: {e}") # <--- МАЯЧОК 5

def save_review(user_id, song_title, review_text):
    """Сохраняет отзыв в лист Reviews"""
    sheet = get_sheet('Reviews')
    if not sheet: return
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([now, user_id, song_title, review_text])
