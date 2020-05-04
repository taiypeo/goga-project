from . import dispatcher
from ..database import thread_local_session, User, Group, Permission, Perm, add_to_database
from telegram.ext import CommandHandler


def create_group(update, context):
    tg_id = update.effective_user.id

    def reply(msg):
        context.bot.send_message(chat_id=update.effective_chat.id, text=(msg))

    with thread_local_session() as session:
        user = session.query(User).filter_by(tg_id=tg_id).first()
        if user is None:
            return reply(
                "Пользователь не найден в системе. "
                "Попробуйте воспользоваться командой '/start'."
            )

        if context.args is None or context.args == []:
            return reply("Название группы не может быть пустым.")

        group_title = " ".join(context.args)
        if group_title == "":
            return reply("Название группы не может быть пустым.")

        group = Group(title=group_title)

        perm = Permission(group=group, user=user, perm=Perm.all())

        if not add_to_database([group, perm], session):
            return reply(
                    "Не удалось создать группу. Попробуйте еще "
                    "раз или обратитесь к администратору."
                ),
        else:
            return reply("Группа успешно создана!")



create_group_handler = CommandHandler("create_group", create_group)
dispatcher.add_handler(create_group_handler)
