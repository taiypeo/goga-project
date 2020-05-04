from ..config import bot_token
from telegram.ext import Updater

updater = Updater(token=bot_token, use_context=True)
dispatcher = updater.dispatcher

from .helloworld import *
from .start import *

updater.start_polling()
