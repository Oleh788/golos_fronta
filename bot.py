import os
import telebot
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))

bot = telebot.TeleBot(BOT_TOKEN)

pending = {}
counter = 0

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

bot.infinity_polling()
