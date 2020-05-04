from . import dispatcher
from ..database import (
    Session,
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


def invite_entry(update, context):
    session = Session()

    tg_id = update.effective_user.id
    user = session.query(User).filter_by(tg_id=tg_id).first()
    if user is None:
        Session.remove()
        raise EffectiveUserNotFound()

    if context.args is None or context.args == []:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Название группы не может быть пустым.",
        )
        Session.remove()
        return ConversationHandler.END

    group_title = " ".join(context.args)
    if group_title == "":
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Название группы не может быть пустым.",
        )
        Session.remove()
        return ConversationHandler.END

    group = session.query(Group).filter_by(title=group_title).first()
    if group is None:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Группа не найдена.",
        )
        Session.remove()
        return ConversationHandler.END

    context.user_data["user"] = user
    context.user_data["group"] = group

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "Введите полномочия для инвайта через пробел "
            "(post, invite_posters, invite_students)."
        ),
    )

    return "GET_PERMISSIONS"


def invite_permissions(update, context):
    if (
        "user" not in context.user_data
        or "group" not in context.user_data
        or not isinstance(context.user_data["user"], User)
        or not isinstance(context.user_data["group"], Group)
    ):
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Неизвестная ошибка. Обратитесь к администратору.",
        )
        Session.remove()
        return ConversationHandler.END

    user = context.user_data["user"]
    group = context.user_data["group"]

    perm_map = {
        "post": Perm.post,
        "invite_posters": Perm.invite_posters,
        "invite_students": Perm.invite_students,
    }

    if update.message is None or update.message.text == "":
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Строка полномочий не может быть пустой.",
        )
        Session.remove()
        return ConversationHandler.END

    invitee_perm = 0
    for perm in update.message.text.split():
        if perm not in perm_map:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Такого полномочия не существует.",
            )
            Session.remove()
            return ConversationHandler.END

        invitee_perm |= perm_map[perm]

    try:
        invitation = user.create_invitation(invitee_perm, group)
    except PermissionError:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="У вас недостаточно полномочий для создания такого инвайта.",
        )
        Session.remove()
        return ConversationHandler.END
    except ValueError:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Вы не состоите в этой группе.",
        )
        Session.remove()
        return ConversationHandler.END

    context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"Ваш созданный инвайт:\n{invitation}",
    )

    Session.remove()
    return ConversationHandler.END


def cancel_invitation(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="Вы отменили создание инвайта.",
    )

    Session.remove()
    return ConversationHandler.END


invite_conversation = ConversationHandler(
    entry_points=[CommandHandler("invite", invite_entry)],
    states={"GET_PERMISSIONS": [MessageHandler(Filters.text, invite_permissions)]},
    fallbacks=[CommandHandler("cancel", cancel_invitation)],
)

dispatcher.add_handler(invite_conversation)
