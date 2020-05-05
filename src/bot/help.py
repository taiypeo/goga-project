from . import dispatcher
from telegram.ext import CommandHandler


def help(update, context):
    help_text = (
        "/help -- показывает все команды\n"
        "/start -- регистрирует пользователя в системе\n"
        "/create_group [название группы] -- создает новую группу\n"
        "/invite [название группы] -- создает новый инвайт в группу\n"
        "/join [инвайт] -- присоединяет пользователя к группе\n"
        "/send [группы через пробел] -- отправить сообщение в группы "
        "(по умолчанию отправляет всем вашим группам)\n"
        "/deadline [группы через пробел] -- обозначить группам дедлайн "
        "(по умолчанию обозначит его всем вашим группам)"
    )

    context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)


help_handler = CommandHandler("help", help)
dispatcher.add_handler(help_handler)
