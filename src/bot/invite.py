from . import dispatcher
from ..database import (
    thread_local_session,
    User,
    Group,
    Permission,
    Perm,
    PermissionError,
    add_to_database,
)
from .exc import EffectiveUserNotFound
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, Filters
from sqlalchemy.orm.session import Session as SessionGetter
from ..config import logger as log


def invite_entry(update, context):
    def reply(msg):
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=msg,
        )

    with thread_local_session() as session:
        tg_id = update.effective_user.id
        user = session.query(User).filter_by(tg_id=tg_id).first()
        if user is None:
            raise EffectiveUserNotFound()

        if context.args is None or context.args == []:
            reply("Название группы не может быть пустым.")
            return ConversationHandler.END

        group_title = " ".join(context.args)
        if group_title == "":
            reply("Название группы не может быть пустым.")
            return ConversationHandler.END

        group = session.query(Group).filter_by(title=group_title).first()
        if group is None:
            reply("Группа не найдена.")
            return ConversationHandler.END

        context.user_data["user_id"] = user.id
        context.user_data["group_id"] = group.id

        reply(
            "Введите полномочия для инвайта через пробел "
            "(post, invite_posters, invite_students)."
        )

        return "GET_PERMISSIONS"


def invite_permissions(update, context):
    def reply(msg):
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=msg,
        )

    with thread_local_session() as session:
        try:
            user = session.query(User).get(context.user_data["user_id"])
            group = session.query(Group).get(context.user_data["group_id"])
        except Exception as e:
            log.error(e)
            reply("Неизвестная ошибка. Обратитесь к администратору.")
            return ConversationHandler.END

        perm_map = {
            "post": Perm.post,
            "invite_posters": Perm.invite_posters,
            "invite_students": Perm.invite_students,
        }

        if update.message is None or update.message.text == "":
            reply("Строка полномочий не может быть пустой.")
            return ConversationHandler.END

        invitee_perm = 0
        for perm in update.message.text.split():
            if perm not in perm_map:
                reply("Такого полномочия не существует.")
                return ConversationHandler.END

        invitee_perm |= perm_map[perm]

        try:
            invitation = user.create_invitation(Perm(invitee_perm), group)
        except PermissionError:
            reply("У вас недостаточно полномочий для создания такого инвайта.")
            return ConversationHandler.END
        except ValueError:
            reply("Вы не состоите в этой группе.")
            return ConversationHandler.END

        reply(f"Ваш созданный инвайт:\n{invitation}")

        return ConversationHandler.END


def cancel_invitation(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="Вы отменили создание инвайта.",
    )

    return ConversationHandler.END


invite_conversation = ConversationHandler(
    entry_points=[CommandHandler("invite", invite_entry)],
    states={"GET_PERMISSIONS": [MessageHandler(Filters.text & (~Filters.command), invite_permissions)]},
    fallbacks=[CommandHandler("cancel", cancel_invitation)],
)

dispatcher.add_handler(invite_conversation)
