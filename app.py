import os
import telebot
from flask import Flask, request
from handlers import register_handlers
from config import TG_TOKEN, ADMIN_ID

# Render сам назначит порт
PORT = int(os.environ.get("PORT", 5000))

bot = register_handlers()
app = Flask(__name__)

WEBHOOK_URL_PATH = "/webhook/"

@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return 'Error', 403

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)