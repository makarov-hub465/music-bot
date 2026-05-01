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

    # --- Сразу после фото показываем кнопку для открытия меню ---
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_menu = types.KeyboardButton("📂 Главное меню")
    markup.add(btn_menu)
    
    bot.send_message(
        user_id, 
        "Нажми кнопку ниже, чтобы открыть меню:",
        reply_markup=markup
    )

# --- КОМАНДА /MENU (Возврат клавиатуры) ---
@bot.message_handler(commands=['menu'])
def show_menu_command(message):
    # Вызываем ту же логику, что и при нажатии на кнопку "Главное меню"
    show_main_menu(message)

# --- Обработчик нажатия на кнопку "📂 Главное меню" ---
@bot.message_handler(func=lambda message: message.text == "📂 Главное меню")
def show_main_menu(message):
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
    user_id = message.from_user.id
    
    songs = database.get_catalog(sort_by_rating=True)
    
    if not songs:
        bot.send_message(user_id, "Каталог пока пуст.")
        return
    
    top_songs = songs[:3]
    
    # --- ХАК ДЛЯ ПРОВЕРКИ СОРТИРОВКИ ---
    # Бот пришлет тебе текстовый список того, что он собирается играть
    # debug_text = "📊 Проверка сортировки:\n"
    # for s in top_songs:
    #    debug_text += f"• {s['title']} (Рейтинг: {s['rating']})\n"
    
    # bot.send_message(user_id, debug_text) 
    # -----------------------------------

    media_group = []
    
    for song in top_songs:
        file_id = song.get('file_id')
        title = song['title']
        
        if file_id and len(file_id) > 10:
            media = types.InputMediaAudio(
                media=file_id,
                caption=f"🎶 {title}"
            )
            media_group.append(media)

    if media_group:
        try:
            bot.send_media_group(user_id, media_group)
            # bot.send_message(user_id, "🎧 Приятного прослушивания!") # Можно убрать, чтобы не спамить
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")
            bot.send_message(user_id, f"Ошибка отправки: {e}")
    else:
        bot.send_message(user_id, "Нет треков для отображения.")

# --- 3. КАТАЛОГ ПЕСЕН (НОВОЕ МЕНЮ С КНОПКАМИ) ---
@bot.message_handler(func=lambda message: message.text == "🎵 Весь каталог")
def show_catalog_menu(message):
    user_id = message.from_user.id
    songs = database.get_catalog(sort_by_rating=False)
    
    if not songs:
        bot.send_message(user_id, "Каталог пуст.")
        return

    # Ограничиваем до 15 песен для удобства интерфейса
    if len(songs) > 15:
        songs = songs[:15]

    # Создаем клавиатуру: каждая песня - отдельная кнопка
    markup = types.InlineKeyboardMarkup(row_width=1) # Кнопки друг под другом
    
    for song in songs:
        title = song['title']
        song_id = song['id']
        # Кнопка с названием песни. При нажатии вызываем play_song_with_buttons
        btn = types.InlineKeyboardButton(f"▶️ {title}", callback_data=f"play_song_{song_id}")
        markup.add(btn)

    bot.send_message(
        user_id, 
        "🎵 <b>Весь каталог:</b>\nНажмите на название, чтобы прослушать и оценить:", 
        parse_mode='HTML', 
        reply_markup=markup
    )

# --- Обработчик нажатия на кнопку песни (Вместо старого play_song) ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('play_song_'))
def play_song_with_buttons(call):
    song_id = call.data.split('_')[2] # Извлекаем ID из callback_data (play_song_ID)
    user_id = call.from_user.id
    
    # Ищем песню по ID в словаре, который возвращает get_catalog
    all_songs = database.get_catalog()
    # Так как get_catalog теперь возвращает список словарей, ищем по ключу 'id'
    song = next((s for s in all_songs if str(s['id']) == str(song_id)), None)
    
    if not song:
        bot.answer_callback_query(call.id, text="Песня не найдена", show_alert=True)
        return

    file_id = song.get('file_id')
    title = song['title']
    
    if file_id:
        # Кнопки под плеером
        markup = types.InlineKeyboardMarkup()
        btn_vote = types.InlineKeyboardButton("👍 Голосовать (+1)", callback_data=f"vote_{song_id}")
        btn_review = types.InlineKeyboardButton("💬 Оставить отзыв", callback_data=f"review_{song_id}")
        markup.row(btn_vote, btn_review)
        
        # Отправляем аудио с кнопками через file_id (быстро!)
        bot.send_audio(
            user_id, 
            audio=file_id, 
            caption=f"🎶 <b>{title}</b>",
            parse_mode='HTML',
            reply_markup=markup
        )
        
        bot.answer_callback_query(call.id) # Убираем индикатор загрузки
    else:
        bot.answer_callback_query(call.id, text="Ошибка файла (нет ID)", show_alert=True)
                
        # 5. Финальный отчет
        bot.send_message(user_id, f"✅ Готово! Отправлено треков: {total_sent}")
        
    except Exception as e:
        # 6. Если случилась ошибка - пишем её текст
        bot.send_message(user_id, f"❌ Произошла ошибка:\n{str(e)}")

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

# --- 5. ГОЛОСОВАНИЕ (Бывшие Лайки) ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('vote_'))
def handle_vote(call):
    song_id = call.data.split('_')[1]
    success = database.vote_for_song(song_id)
    
    if success:
        bot.answer_callback_query(call.id, text="✅ Голос учтен!", show_alert=True)
    else:
        bot.answer_callback_query(call.id, text="❌ Ошибка голосования", show_alert=True)

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
    
    # Находим название песни через базу данных (словари)
    songs = database.get_catalog()
    song_title = "Неизвестная песня"
    for s in songs:
        if str(s['id']) == str(song_id):
            song_title = s['title']
            break
            
    # 1. СОХРАНЯЕМ В ТАБЛИЦУ
    database.save_review(user_id, song_title, review_text)
            
    # 2. Уведомляем админа
    admin_msg = f"💬 <b>Новый отзыв на '{song_title}'</b>\nОт: @{message.from_user.username}\nТекст: {review_text}"
    bot.send_message(ADMIN_ID, admin_msg, parse_mode='HTML')
    
    bot.send_message(user_id, "✅ Спасибо за твой отзыв! Он сохранен.")
    
    del review_states[user_id]

# --- 6. ЗАКАЗ СТИХА (Логика состояний) ---
@bot.message_handler(func=lambda message: message.text == "✍️ Заказать стих")
def start_order(message):
    print(f"🔥 КНОПКА НАЖАТА! Устанавливаю состояние для {message.from_user.id}")
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
    # Этот принт появится ТОЛЬКО если условие выше выполнилось
    print(f"🚀 ХЕНДЛЕР ЗАКАЗА СРАБОТАЛ! Текст: {message.text}") 
    
    user_id = message.from_user.id
    details = message.text
    
    # ... остальной код
    
    # 1. Сохраняем в базу
    database.add_order(user_id, details, bot=bot, admin_id=ADMIN_ID)
    
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
