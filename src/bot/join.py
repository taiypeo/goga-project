from . import dispatcher
from .exc import EffectiveUserNotFound
from ..database import (
    thread_local_session,
    User,
    Group,
    Permission,
    Perm,
    add_to_database,
    AlreadyJoinedError,
    NonexistantGroup,
    BadInvitation
)
from telegram.ext import CommandHandler
from itsdangerous.exc import BadSignature
from sqlalchemy.orm.exc import MultipleResultsFound


def join(update, context):
    tg_id = update.effective_user.id

    def reply(msg):
        context.bot.send_message(chat_id=update.effective_chat.id, text=(msg))

    with thread_local_session() as session:
        user = session.query(User).filter_by(tg_id=tg_id).first()
        if user is None:
            raise EffectiveUserNotFound()

        if context.args is None or context.args == []:
            return reply("Инвайт не может быть пустым.")

        invitation = " ".join(context.args)
        if invitation == "":
            return reply("Инвайт не может быть пустым.")

        try:
            group = user.accept_invite(invitation)
        except (BadInvitation, NonexistantGroup):
            return reply("Невалидный инвайт.")
        except AlreadyJoinedError:
            return reply("Вы уже состоите в этой группе.")

        return reply(f"Вы успешно присоединились к группе '{group.title}'!")


join_handler = CommandHandler("join", join)
dispatcher.add_handler(join_handler)
