import logging
import os
import sys
import telegram
from telegram.ext import Dispatcher, Updater, CommandHandler, MessageHandler, Filters
import time

def test_db():
    from database import session, User, ROLE_STUDENT, Event

    u = User(telegram_id=str(int(time.time())), role=ROLE_STUDENT)
    print(u)
    
    session.add(u)
    for i in range(7):
        e = Event(expired=(i % 2 == 0))
        session.add(e)
        u.events.append(e)
    session.commit()

    print(*Event.upcoming_events(session, 2), sep='\n')

test_db()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

if "TG_BOT_TOKEN" not in os.environ:
    logger.critical("No TG_BOT_TOKEN environment variable found")
    sys.exit(1)

bot = telegram.Bot(token=os.environ["TG_BOT_TOKEN"])
print(bot.get_me())

prejoined_users = set()
pregenerating = defaultdict({"step":0})

updater = Updater(token = os.environ["TG_BOT_TOKEN"])
dispatcher = updater.dispatcher

def prejoin(update, context):
    user_id = update.effective_chat.id
    prejoined_users.add(user_id)
    context.bot.send_message(chat_id=user_id, text="Хорошо, жду ваш токен.")

prejoin_handler = CommandHandler('join', prejoin)
dispatcher.add_handler(join_handler)

def join(update, context):
    user_id = update.effective_chat.id
    if user_id in prejoined_users:
        token = update.message.text
	prejoined_users.remove(user_id)
        if 'token in token list':
            'give permissions according to token'

join_handler = MessageHandler(Filters.text & (~Filters.command), join)

def ask_token_type(update, context):
    user_id = update.effective.chat.id
    if 'dude has only one type of permitted token':
        pregenerating[user_id]["type"] = 'type'
        pregenerating[user_id]["step"] += 2
	context.bot.send_message(chat_id=user_id, text="Укажите группу.")
    else:
        context.bot.send_message(chat_id=user_id, text="Укажите тип токена [админ, преподаватель, ученик].")
        pregenerating[user_id]["step"] += 1
        return;

def handle_token_type(update, context):
    user_id = update.effective.chat.id
    token_type = update.message.text
    match = {"админ":"admin", "преподаватель":"teacher", "ученик":"student"}
    if token_type in keys(match):
        pregenerating[user_id]["type"] = match[token_type]
        pregenerating[user_id]["step"] += 1
        context.bot.send_message(chat_id=user_id, text="Укажите группу.")
    else:
        context.bot.send_message(chat_id=user_id, text="Такого типа токена не существует. Попробуйте ещё раз.")

def handle_group(update, context):
    user_id = update.effective.chat.id
    group = update.message.text
    if 'dude has permission to give tokens for this group':
        token = secrets.token_hex(18)
	'write everything to db'
        del pregenerating[user_id]
	context.bot.send_message(chat_id=user_id, text=f"Токен успешно создан. Не рекомендуется выкладывать его в открытый доступ.")
	context.bot.send_message(chat_id=user_id, text=token)
    else:
        context.bot.send_message(chat_id=user_id, text="У вас нет разрешения выдавать такие токены для этой группы. Попробуйте ещё раз")


token_progress = [ask_token_type, handle_token_type, handle_group]

def handle_token_dialog(update, context):
    user_id = update.effective.chat.id
    token_progress[pregenerating[user_id]["step"]](update, context)

def handle_token_command(update, context):
    user_id = update.effective.chat.id
    if 'dude has no rights to give tokens':
        context.bot.send_message(chat_id=user_id, text="Извините, у вас не прав выдавать токены.")
        return;

    handle_token_dialog(update, context)

token_handler = CommandHandler('token', handle_token_command)
dispatcher.add_handler(token_handler)

token_dialog_handler = MessageHandler(Filters.text & (~Filters.command), handle_token_dialog)
dispatcher.add_handler(token_dialog_handler)



