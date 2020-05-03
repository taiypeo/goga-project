import logging
import os
import sys
import telegram

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
