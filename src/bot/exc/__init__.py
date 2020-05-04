from .. import dispatcher
from telegram.error import TelegramError
from ...config import logger as log
from io import StringIO
from traceback import print_exc


class BotErrorHandler(RuntimeError):
    def teardown(self, update, context):
        raise NotImplementedError("Do not use BotErrorHandler directly")


class EffectiveUserNotFound(BotErrorHandler):
    def teardown(self, update, context):
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=("Чтобы начать пользоваться ботом, отправьте '/start'."),
        )


def handle_errors(update, context):
    try:
        raise context.error
    except BotErrorHandler as handler:
        handler.teardown(update, context)
    except Exception:
        io = StringIO()
        print_exc(file=io)
        log.error("\n" + io.getvalue())
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Неизвестная ошибка внутри бота"
        )


dispatcher.add_error_handler(handle_errors)
