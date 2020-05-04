import sys
import logging
from os import environ

logger = logging.getLogger()
logger.setLevel(level=environ.get("LOGLEVEL", "ERROR").upper())

if "TG_BOT_TOKEN" not in environ:
    logger.critical("No TG_BOT_TOKEN environment variable found")
    sys.exit(1)

bot_token = environ["TG_BOT_TOKEN"]
