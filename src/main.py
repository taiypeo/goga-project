import logging
import os
import sys
from typing import Dict, Tuple, List
from logging import info

import telegram
from telegram.ext import Dispatcher, Updater, CommandHandler, MessageHandler, Filters
import time
from collections import defaultdict
import secrets
from database import (
    get_users,
    add_token,
    check_token_presence,
    add_permission,
    check_permissions,
    session,
    User,
    UnbindedPermissions
)

from config import bot_token

admin = UnbindedPermissions(
    "post", "create_subgroups", "invite_admins", "invite_posters", "invite_students"
)
teacher = UnbindedPermissions("post")
student = UnbindedPermissions()

god_token = secrets.token_hex(18)
add_token(god_token, "root", admin)
print("Your universal token:")
print(god_token)
del god_token

joining_users = set()
new_token_records = defaultdict(lambda: {"step": 0})
mew_msg_records = defaultdict(lambda: {"step": 0})

updater = Updater(token=bot_token, use_context=True)
dispatcher = updater.dispatcher


def prejoin(update, context):
    user_id = update.effective_chat.id
    joining_users.add(user_id)
    context.bot.send_message(
        chat_id=user_id, text="Хорошо, жду ваш токен.{}".format(joining_users)
    )


prejoin_handler = CommandHandler("join", prejoin)
dispatcher.add_handler(prejoin_handler)


def join(update, context):
    user_id = update.effective_chat.id
    context.bot.send_message(chat_id=user_id, text=user_id)
    if user_id in joining_users:
        token_str: str = update.message.text
        joining_users.remove(user_id)
        token = session.query(Token).filter_by(token=token_str)
        if token is not None:
            info(f'chat_id={user_id}, "TOKEN_OK"')
            context.bot.send_message(
                chat_id=user_id, text="{}, {}".format(token.course.title, token.permissions)
            )
            add_permission(user_id, course, permissions)
            context.bot.send_message(chat_id=user_id, text="1")
            report = f"Теперь в пределах группы {token.course.title} вы можете"
            ru_names = (
                "отправлять сообщения",
                "создавать подгруппы",
                "приглашать админов",
                "приглашать учителей",
                "приглашать студентов",
            )
            context.bot.send_message(chat_id=user_id, text="2")

            report = report + ", ".join(
                [ru_names[i] for i in range(1, len(permissions)) if permissions[i] > 0]
            )
            context.bot.send_message(chat_id=user_id, text="3")

            context.bot.send_message(chat_id=user_id, text=report)
        else:
            context.bot.send_message(chat_id=user_id, text="У вас неверный токен")


join_handler = MessageHandler(Filters.text & (~Filters.command), join)
dispatcher.add_handler(join_handler)


def can_give_tokens(user_id: int) -> Tuple[bool, bool, bool]:
    users = get_users(user_id)
    return (
        any(user.permissions.enabled('invite_admins') for user in users),
        any(user.permissions.enabled('invite_posters') for user in users),
        any(user.permissions.enabled('invite_students') for user in users),
    )


def ask_token_type(update, context):
    user_id = update.effective_chat.id
    match = (admin, teacher, student)
    can_give = can_give_tokens(user_id)
    if sum(can_give) == 1:
        new_token_records[user_id]["perm"] = match[can_give.index(True)]
        new_token_records[user_id]["step"] += 2
        context.bot.send_message(chat_id=user_id, text="Укажите группу.")
    else:
        context.bot.send_message(
            chat_id=user_id, text="Укажите тип токена [админ, преподаватель, ученик]."
        )
        new_token_records[user_id]["step"] += 1


def handle_token_type(update, context):
    user_id: int = update.effective_chat.id
    token_type: str = context.args[0]
    match: Dict[str, Tuple[int, int, int, int, int]] = {
        "admin": admin,
        "teacher": teacher,
        "pupil": student,
    }
    if token_type in match.keys():
        new_token_records[user_id]["perm"] = match[token_type]
        new_token_records[user_id]["step"] += 1
        context.bot.send_message(chat_id=user_id, text="Укажите группу.")
    else:
        context.bot.send_message(
            chat_id=user_id,
            text="Такого типа токена не существует. Попробуйте ещё раз.",
        )


def all_admined_courses(user_id: int) -> List[str]:
    users = get_users(user_id)
    return list(
        user for user in users
        if user.permissions.enabled('invite_admins') or
           user.permissions.enabled('invite_posters') or
           user.permissions.enabled('invite_students')
    )


def handle_tk_group(update, context):
    user_id = update.effective_chat.id
    group = context.args[0]

    if group in all_admined_courses(user_id):
        token = secrets.token_hex(18)
        add_token(token, group, new_token_records[user_id]["perm"])
        del new_token_records[user_id]
        context.bot.send_message(
            chat_id=user_id,
            text=f"Токен успешно создан. Не рекомендуется выкладывать его в открытый доступ.",
        )
        context.bot.send_message(chat_id=user_id, text=token)
    else:
        context.bot.send_message(
            chat_id=user_id,
            text="У вас нет разрешения выдавать такие токены для этой группы. Попробуйте ещё раз",
        )


token_progress = [ask_token_type, handle_token_type, handle_tk_group]


def handle_token_dialog(update, context):
    user_id = update.effective_chat.id
    context.bot.send_message(chat_id=user_id, text=new_token_records[user_id])
    context.bot.send_message(chat_id=user_id, text=context.args)
    token_progress[new_token_records[user_id]["step"]](update, context)


def handle_token_command(update, context):
    user_id = update.effective_chat.id
    if not any(can_give_tokens(user_id)):
        context.bot.send_message(
            chat_id=user_id, text="Извините, у вас не прав выдавать токены."
        )
        return

    handle_token_dialog(update, context)


token_handler = CommandHandler("token", handle_token_command)
dispatcher.add_handler(token_handler)

token_dialog_handler = MessageHandler(
    Filters.text & (~Filters.command), handle_token_dialog
)
dispatcher.add_handler(token_dialog_handler)


def ask_group(update, context):
    user_id = update.effective_chat.id
    send_courses = [
        user for user in get_users(user_id) if user.permissions.enabled('post')
    ]

    if len(send_courses) == 1:
        mew_msg_records[user_id]["group"] = send_courses[
            0
        ].title  # TODO: Олег, так нужно?
        mew_msg_records[user_id]["step"] += 2
        context.bot.send_message(
            chat_id=user_id,
            text="Если хотите обозначить дедлайн, напишите его в формате\
         ГГ.ММ.ДД ЧЧ:ММ. Если нет, просто поставьте '-'.",
        )
        return

    mew_msg_records[user_id]["step"] += 1
    context.bot.send_message(
        chat_id=user_id, text="Укажите группу, в которую хотите отправить сообщение."
    )


def handle_send_group(update, context):
    user_id = update.effective_chat.id
    group = update.message.text
    if check_permissions(user_id, group, (True, None, None, None, None)):
        mew_msg_records[user_id]["step"] += 1
        context.bot.send_message(
            chat_id=user_id,
            text="Если хотите обозначить дедлайн, напишите его в формате\
                 ГГ.ММ.ДД ЧЧ:ММ. Если нет, просто поставьте '-'.",
        )
    else:
        context.bot.send_message(chat_id=user_id, text="У вас нет права отсылать ")


def handle_send(update, context):
    user_id = update.effective_chat.id
    send_courses = [
        user for user in get_users(user_id) if user.permissions.enabled('post')
    ]

    if len(send_courses) == 0:
        context.bot.send_message(
            chat_id=user_id, text="Извините, у вас нет права отправлять сообщения."
        )
        return

    if len(send_courses) == 1:
        mew_msg_records[user_id]["group"] = send_courses[
            0
        ].title  # TODO: Олег, так нужно?
        mew_msg_records[user_id]["step"] += 2
        context.bot.send_message(
            chat_id=user_id,
            text="Если хотите обозначить дедлайн, напишите его в формате\
         ГГ.ММ.ДД ЧЧ:ММ. Если нет, просто поставьте '-'.",
        )


updater.start_polling()

updater.idle()
