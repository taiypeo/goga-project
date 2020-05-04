from .. import dispatcher
from telegram.error import TelegramError
from ...config import logger as log
from io import StringIO
from traceback import print_exc

def handle_errors(update, context):
    try:
        raise context.error
    except Exception:
        io = StringIO()
        print_exc(file=io)
        log.error('\n' + io.getvalue())
        context.bot.send_message(chat_id=update.effective_chat.id, text='Неизвестная ошибка внутри бота')


dispatcher.add_error_handler(handle_errors)
