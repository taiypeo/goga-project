import random

import os

TOKEN = os.environ["TG_BOT_TOKEN"]

from telegram.ext import Updater

updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


# START
def start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I'm a bot for your timetable&deadlines! There will be help for commands",
    )


from telegram.ext import CommandHandler

start_handler = CommandHandler("start", start)
dispatcher.add_handler(start_handler)


# REGISTER USER
def join(update, context):
    try:
        token = context.args[0]
    except:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Fuck you! Your token is bullshit!"
        )
        return
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="registering you with token:{}...".format(token),
    )
    reg_result = "ok"  # db_register_user(token, update.effective_chat.id)


register_handler = CommandHandler("join", join)
dispatcher.add_handler(register_handler)


def create_token(update, context):
    permissions = context.args
    token = "aaa"  # db_get_token(permissions)
    context.bot.send_message(chat_id=update.effective_chat.id, text=token)


create_token_handler = CommandHandler("token", create_token)
dispatcher.add_handler(create_token_handler)

# MY_DEADLINES
def get_deadlines(update, context):
    deadlines = "aaa"  # db_get_deadlines(update.effective_chat.id, context.args)
    context.bot.send_message(chat_id=update.effective_chat.id, text=deadlines)


deadlines_handler = CommandHandler("deadlines", get_deadlines)
dispatcher.add_handler(deadlines_handler)

updater.start_polling()
updater.idle()
