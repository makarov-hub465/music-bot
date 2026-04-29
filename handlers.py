import telebot
from telebot import types
import os
import database
from config import BOT_TOKEN, ADMIN_ID

bot = telebot.TeleBot(BOT_TOKEN)

# --- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ (Обязательно на этом уровне, без отступов!) ---
user_states = {}
review_states = {} 

# --- 1. СТАРТ И ПРИВЕТСТВИЕ С КАРТИНКОЙ ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or "Гость"
    
    # Регистрируем пользователя
    database.add_user(user_id, name)
    
    # Отправляем картинку-заставку
    try:
        with open('welcome.jpg', 'rb') as photo:
            bot.send_photo(
                user_id, 
                photo, 
                caption=(
                    f"🎸 <b>Привет, {name}!</b>\n\n"
                    f"Это официальный музыкальный канал <b>Сергея Макарова</b> — автора текстов для песен.\n\n"
                    f"Здесь ты можешь:\n"
                    f"• Слушать мои треки 🎧\n"
                    f"• Оценивать и оставлять отзывы 💬\n"
                    f"• Заказать поздравление юбиляру, текст песни, переделку известной песни ✍️"
                ),
                parse_mode='HTML'
            )
    except Exception as e:
        # Если картинки нет, просто шлем текст
        print(f"Ошибка отправки фото: {e}")
        bot.send_message(user_id, f"Привет, {name}! 🎸 Я музыкальный ассистент.")

    # --- КОМАНДА /MENU (Возврат клавиатуры) ---
@bot.message_handler(commands=['menu'])
def show_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_top = types.KeyboardButton("🔥 Топ-3 Хита")
    btn_catalog = types.KeyboardButton("🎵 Весь каталог")
    btn_order = types.KeyboardButton("✍️ Заказать стих")
    btn_donate = types.KeyboardButton("☕ Поддержать автора")
    
    markup.row(btn_top, btn_catalog)
    markup.row(btn_order, btn_donate)
    
    bot.send_message(message.from_user.id, "📂 Главное меню:", reply_markup=markup)

# --- 2. ТОП-10 ХИТОВ (ИСПРАВЛЕННАЯ ВЕРСИЯ) ---
@bot.message_handler(func=lambda message: message.text == "🔥 Топ-3 Хита")
def send_top_hits(message):
    songs = database.get_catalog(sort_by_rating=True)
    if not songs:
        bot.send_message(message.from_user.id, "Каталог пока пуст.")
        return
    
    top_songs = songs[:3]
    media_group = []
    opened_files = [] # Список для хранения открытых файлов, чтобы они не закрылись раньше времени
    
    for row in top_songs:
        filename = row[2]
        title = row[1]
        file_path = os.path.join('music', filename)
        
        if os.path.exists(file_path):
            try:
                # Открываем файл и сохраняем ссылку на него
                f = open(file_path, 'rb')
                opened_files.append(f) 
                
                media = types.InputMediaAudio(
                    media=f, # Передаем открытый объект файла
                    caption=title,
                    parse_mode='HTML'
                )
                media_group.append(media)
            except Exception as e:
                print(f"❌ Ошибка чтения файла {filename}: {e}")
        else:
            print(f"⚠️ Файл не найден: {file_path}")

    if media_group:
        try:
            bot.send_media_group(message.from_user.id, media_group)
            bot.send_message(message.from_user.id, "🎧 Приятного прослушивания!")
        except Exception as e:
            print(f"❌ Ошибка отправки группы: {e}")
            bot.send_message(message.from_user.id, "Не удалось отправить альбом.")
        finally:
            # Обязательно закрываем все файлы после отправки (или ошибки)
            for f in opened_files:
                f.close()
    else:
        bot.send_message(message.from_user.id, "Нет доступных файлов.")

# --- 3. КАТАЛОГ ПЕСЕН (СПИСОК) ---
@bot.message_handler(func=lambda message: message.text == "🎵 Весь каталог")
def show_catalog(message):
    songs = database.get_catalog()
    if not songs:
        bot.send_message(message.from_user.id, "Каталог пуст.")
        return
    
    markup = types.InlineKeyboardMarkup()
    for row in songs:
        song_id = row[0]
        title = row[1]
        # callback_data будет вида: play_1
        markup.add(types.InlineKeyboardButton(text=f"🎧 {title}", callback_data=f"play_{song_id}"))
        
    bot.send_message(message.from_user.id, "Выбери трек:", reply_markup=markup)

# --- 4. ВОСПРОИЗВЕДЕНИЕ ОДНОЙ ПЕСНИ ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('play_'))
def play_song(call):
    song_id = call.data.split('_')[1]
    songs = database.get_catalog()
    
    song_data = None
    for row in songs:
        if row[0] == song_id:
            song_data = row
            break
            
    # ИСПРАВЛЕННАЯ СТРОКА НИЖЕ:
    if not song_data:
        bot.answer_callback_query(call.id, "Песня не найдена")
        return
        
    title = song_data[1]
    filename = song_data[2]
    description = song_data[3]
    file_path = os.path.join('music', filename)
    
    if not os.path.exists(file_path):
        bot.send_message(call.from_user.id, "Файл не найден на сервере 😔")
        return
    
    # Отправляем аудио
    with open(file_path, 'rb') as audio:
        bot.send_audio(
            call.from_user.id, 
            audio, 
            caption=f"🎶 <b>{title}</b>\n\n{description}",
            parse_mode='HTML'
        )
    
    # Кнопки под песней
    markup = types.InlineKeyboardMarkup()
    btn_like = types.InlineKeyboardButton("👍 Нравится", callback_data=f"like_{song_id}")
    btn_review = types.InlineKeyboardButton("💬 Написать отзыв", callback_data=f"review_{song_id}")
    markup.add(btn_like, btn_review)
    
    bot.send_message(call.from_user.id, "Как тебе трек?", reply_markup=markup)
    bot.answer_callback_query(call.id)

# --- 5. ЛАЙКИ ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('like_'))
def like_song(call):
    song_id = call.data.split('_')[1]
    database.update_rating(song_id)
    bot.answer_callback_query(call.id, "Спасибо за лайк! ❤️")
    bot.send_message(call.from_user.id, "Твой голос учтен в рейтинге!")

# --- ОБРАБОТКА ОТЗЫВОВ ---

@bot.callback_query_handler(func=lambda call: call.data.startswith('review_'))
def start_review(call):
    song_id = call.data.split('_')[1]
    user_id = call.from_user.id
    
    # Запоминаем, для какой песни пользователь хочет оставить отзыв
    review_states[user_id] = song_id
    
    bot.answer_callback_query(call.id)
    bot.send_message(
        user_id, 
        "✍️ Напиши свой отзыв об этом треке:\n(Чтобы отменить, напиши /cancel)"
    )

@bot.message_handler(func=lambda message: message.from_user.id in review_states)
def process_review(message):
    user_id = message.from_user.id
    song_id = review_states[user_id]
    review_text = message.text
    
    # Находим название песни
    songs = database.get_catalog()
    song_title = "Неизвестная песня"
    for row in songs:
        if row[0] == song_id:
            song_title = row[1]
            break
            
    # 1. СОХРАНЯЕМ В ТАБЛИЦУ (Новая строка)
    database.save_review(user_id, song_title, review_text)
            
    # 2. Уведомляем админа
    admin_msg = f"💬 <b>Новый отзыв на '{song_title}'</b>\nОт: @{message.from_user.username}\nТекст: {review_text}"
    bot.send_message(ADMIN_ID, admin_msg, parse_mode='HTML')
    
    bot.send_message(user_id, "✅ Спасибо за твой отзыв! Он сохранен.")
    
    del review_states[user_id]

# --- 6. ЗАКАЗ СТИХА (Логика состояний) ---
@bot.message_handler(func=lambda message: message.text == "✍️ Заказать стих")
def start_order(message):
    user_id = message.from_user.id
    user_states[user_id] = 'waiting_for_details'
    
    bot.send_message(
        user_id, 
        "Отлично! Напиши мне кратко:\n"
        "- Кому посвящаем?\n"
        "- Какой повод?\n"
        "- Главные пожелания или ключевые слова.\n\n"
        "(Чтобы отменить, напиши /cancel)"
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'waiting_for_details')
def process_order(message):
    user_id = message.from_user.id
    details = message.text
    
    # 1. Сохраняем в базу
    database.add_order(user_id, details)
    
    # 2. Уведомляем админа (тебя)
    admin_msg = (
        f"🔥 <b>Новый заказ!</b>\n"
        f"От: @{message.from_user.username} (ID: {user_id})\n"
        f"Текст: {details}"
    )
    bot.send_message(ADMIN_ID, admin_msg, parse_mode='HTML')
    
    # 3. Ответ клиенту
    bot.send_message(user_id, "✅ Заявка принята! Я свяжусь с тобой в ближайшее время для уточнения деталей.")
    
    # Сбрасываем состояние
    user_states[user_id] = None

# Команда отмены
@bot.message_handler(commands=['cancel'])
def cancel_order(message):
    user_id = message.from_user.id
    if user_states.get(user_id) == 'waiting_for_details':
        user_states[user_id] = None
        bot.send_message(user_id, "❌ Заказ отменен.")
    else:
        bot.send_message(user_id, "У вас нет активного заказа.")

# --- 7. ДОНАТЫ ---
@bot.message_handler(func=lambda message: message.text == "☕ Поддержать автора")
def donate(message):
    from config import DONATE_LINK
    
    markup = types.InlineKeyboardMarkup()
    # Кнопка-ссылка, которая откроет браузер
    markup.add(types.InlineKeyboardButton(text="Перейти к оплате 💳", url=DONATE_LINK))
    
    bot.send_message(
        message.from_user.id, 
        "Спасибо, что ценишь мое творчество! ❤️\n\n"
        "Любая поддержка помогает мне писать новые хиты и развивать канал.\n"
        "Нажми на кнопку ниже, чтобы выбрать сумму:",
        reply_markup=markup
    )

@bot.message_handler(commands=['testfiles'])
def test_files(message):
    import os
    try:
        files = os.listdir('music')
        mp3_files = [f for f in files if f.endswith('.mp3')]
        bot.send_message(message.chat.id, f"Найдено MP3 файлов: {len(mp3_files)}\n{', '.join(mp3_files[:5])}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")

@bot.message_handler(commands=['checkdb'])
def check_db(message):
    try:
        songs = database.get_catalog(sort_by_rating=False) # Берем все без сортировки
        if not songs:
            bot.send_message(message.chat.id, "📭 Таблица пуста или не читается.")
        else:
            # Показываем первые 3 строки из таблицы
            preview = "\n".join([f"{row[1]} - {row[2]}" for row in songs[:3]])
            bot.send_message(message.chat.id, f"📄 В таблице найдено {len(songs)} записей.\n\nПервые 3:\n{preview}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка доступа к БД: {e}")
        
# --- ЗАПУСК ОБРАБОТЧИКОВ ---
def register_handlers():
    return bot
