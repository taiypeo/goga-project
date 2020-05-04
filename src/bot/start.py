from . import dispatcher
from ..database import Session, User, add_to_database
from telegram.ext import CommandHandler


def start(update, context):
    session = Session()
    tg_id = update.effective_user.id

    if session.query(User).filter_by(tg_id=tg_id).first() is not None:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Вы уже были ранее добавлены в систему.")
        Session.remove()
        return  # User already exists

    user = User(tg_id=tg_id)
    if not add_to_database(user, session):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Не удалось зарегистрировать нового пользователя. Попробуйте воспользоваться командой '/start' еще раз, или обратитесь к администратору.")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Новый пользователь успешно добавлен в систему!")

    Session.remove()


start_handler = CommandHandler("start", start)
dispatcher.add_handler(start_handler)
