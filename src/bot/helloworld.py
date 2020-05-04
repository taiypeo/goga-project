from . import dispatcher
from telegram.ext import CommandHandler


def helloworld(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello, world!")


helloworld_handler = CommandHandler("helloworld", helloworld)
dispatcher.add_handler(helloworld_handler)
