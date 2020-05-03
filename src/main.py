import logging
import os
import sys
import telegram
import telegram.ext

def test_db():
    from database import session, User, ROLE_STUDENT

    u = User(telegram_id="1337", role=ROLE_STUDENT)
    print(u)
    session.add(u)
    session.commit()

test_db()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

if "TG_BOT_TOKEN" not in os.environ:
    logger.critical("No TG_BOT_TOKEN environment variable found")
    sys.exit(1)

bot = telegram.Bot(token=os.environ["TG_BOT_TOKEN"])
print(bot.get_me())

updater = Updater(token = os.environ["TG_BOT_TOKEN"])
dispatcher = updater.dispatcher

def preregister(update, context):
    user_id = update.effective_chat.id
    # write user_id to db of preregistered

register_handler = CommandHandler('register', preregister)
dispatcher.add_handler(register_handler)

def register(update, context):
    user_id = update.effective_chat.id
    if 'user_id in preregistered db':
        token = update.message.text
	'remove from preregistered db'
        if 'token in token list':
            'give permissions according to token'


