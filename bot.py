import os
import threading
import telebot
from telebot import types
from flask import Flask

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

pending = {}
counter = 0

@app.route('/')
def home():
    return "Bot is running"

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привет. Напиши сюда свою историю — что произошло, что хочешь рассказать. "
        "Сообщение уйдёт на модерацию анонимно, без твоего имени. "
        "После проверки оно может быть опубликовано в канале."
    )

@bot.message_handler(func=lambda m: True, content_types=['text'])
def handle_message(message):
    global counter
    counter += 1
    msg_id = counter
    pending[msg_id] = message.text

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Опубликовать", callback_data=f"pub_{msg_id}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"rej_{msg_id}")
    )
    bot.send_message(
        ADMIN_ID,
        f"Новое сообщение #{msg_id}:\n\n{message.text}",
        reply_markup=markup
    )
    bot.send_message(message.chat.id, "Спасибо, твоя история отправлена на модерацию.")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    action, msg_id = call.data.split("_")
    msg_id = int(msg_id)
    text = pending.get(msg_id)

    if text is None:
        bot.answer_callback_query(call.id, "Сообщение уже обработано.")
        return

    if action == "pub":
        bot.send_message(CHANNEL_ID, text)
        bot.answer_callback_query(call.id, "Опубликовано.")
        bot.edit_message_text(f"✅ Опубликовано #{msg_id}", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "Отклонено.")
        bot.edit_message_text(f"❌ Отклонено #{msg_id}", call.message.chat.id, call.message.message_id)

    del pending[msg_id]

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
