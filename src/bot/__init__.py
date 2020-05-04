from ..config import bot_token, logger as log
from telegram.ext import Updater

updater = Updater(token=bot_token, use_context=True)
dispatcher = updater.dispatcher

from .helloworld import *
from .start import *
from .create_group import *
from .invite import *

from .exc import *

log.info("start polling...")
updater.start_polling()
