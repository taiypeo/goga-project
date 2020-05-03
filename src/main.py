import logging
import os
import sys
import telegram

logger = logging.getLogger()
logger.setLevel(logging.INFO)

if "TG_BOT_TOKEN" not in os.environ:
    logger.critical("No TG_BOT_TOKEN environment variable found")
    sys.exit(1)

bot = telegram.Bot(token=os.environ["TG_BOT_TOKEN"])
print(bot.get_me())
