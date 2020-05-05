from telegram.ext import CommandHandler, ConversationHandler, CallbackContext, MessageHandler, Filters
from telegram import Update
from ..database import Session, User, Group, Permission, Perm
from .exc import EffectiveUserNotFound
from typing import List, Set
from functools import reduce
from . import dispatcher


def send_entry(update: Update, context: CallbackContext) -> str:
    session: Session = Session()
    tg_id = update.effective_chat.id

    user = session.query(User).filter_by(tg_id=tg_id).first()
    context.user_data["user"] = user

    if user is None:
        Session.remove()
        raise EffectiveUserNotFound()

    permissions: List[Permission] = user.groups
    permitted_groups: Set[Group] = set([perm.group for perm in permissions if (Perm.post in perm.perm)])

    if len(permitted_groups) == 0:
        context.bot.send_message(chat_id=tg_id, text="У вас нет права отсылать сообщения.")
        return ConversationHandler.END

    if context.args is None or context.args == []:
        context.user_data["adr_groups"] = permitted_groups
        return "HANDLE_KEYWORDS"

    adr_group_titles = set(context.args)
    permitted_group_titles = set(map(lambda x: x.title, permitted_groups))
    if not permitted_group_titles >= adr_group_titles:
        context.bot.send_message(f"Вы не можете писать в "
                                 f"{', '.join(adr_group_titles - permitted_group_titles)}.")
        return ConversationHandler.END

    context.user_data["adr_groups"] = set(filter(lambda x: x.title in adr_group_titles,
                                                 permitted_groups))
    context.bot.send_message(chat_id=tg_id,
                             text="Введите ключевые слова через пробел. "
                                  "Отправьте '-' если не хотите добавлять их.")
    return "HANDLE_KEYWORDS"


def handle_keywords(update: Update, context: CallbackContext) -> str:
    text = update.message.text
    keywords: Set[str] = set(map(lambda x: x.strip(), text.split(" ")))
    context.user_data["keywords"] = keywords - {"-"}
    context.bot.send_message(chat_id=update.effective_chat.id, text="Введите сообщение.")
    return "HANDLE_MSG_BODY"


def handle_msg(update: Update, context: CallbackContext) -> str:
    adr_gr: Set[Group] = context.user_data["adr_groups"]

    def to_id_set(x: Group) -> Set[int]:
        return set(map(lambda perm: perm.user.tg_id, x.users))

    id_sets: List[Set[int]] = list(map(to_id_set, adr_gr))
    id_set = reduce(lambda x, y: x | y, id_sets)

    sender_id: int = update.effective_chat.id
    message_id: int = update.message.message_id
    keywords: Set[str] = context.user_data['keywords']

    for tg_id in id_set:
        if len(keywords) > 0:
            context.bot.send_message(tg_id, text=f"Ключевые слова: {' '.join(keywords)}")

        context.bot.forward_message(tg_id, sender_id, message_id)

    return ConversationHandler.END


send_conv = ConversationHandler(entry_points=[CommandHandler("send", send_entry)],
                                states={
                                    "HANDLE_KEYWORDS": [MessageHandler(Filters.text & (~Filters.command),
                                                                       handle_keywords)],
                                    "HANDLE_MSG_BODY": [MessageHandler(Filters.all,
                                                                       handle_msg)]},
                                fallbacks={})
dispatcher.add_handler(send_conv)
