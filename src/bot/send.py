from telegram.ext import CommandHandler, ConversationHandler, CallbackContext, MessageHandler, Filters
from telegram import Update
from ..database import Session, User, Group, Permission, Perm, \
    Message, Deadline, add_to_database, thread_local_session
from .exc import EffectiveUserNotFound
from typing import List, Set
from functools import reduce
from . import dispatcher
import datetime as dt


def send_entry(update: Update, context: CallbackContext) -> str:
    with thread_local_session() as session:
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
            print("no args")
            context.user_data["adr_groups"] = permitted_groups
            context.bot.send_message(chat_id=tg_id,
                                     text="Введите ключевые слова через пробел. "
                                          "Отправьте '-' если не хотите добавлять их.")
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


def send(context: CallbackContext, msg: Message):
    def to_id_set(x: Group) -> Set[int]:
        return set(map(lambda perm: perm.user.tg_id, x.users))

    id_sets: List[Set[int]] = list(map(to_id_set, msg.groups))
    id_set = reduce(lambda x, y: x | y, id_sets)

    for tg_id in id_set:
        if len(msg.keywords) > 0:
            words = map(lambda keyword: keyword.word, msg.keywords)
            context.bot.send_message(tg_id, text=f"Ключевые слова: {' '.join(words)}")

        context.bot.forward_message(tg_id, msg.user.tg_id, msg.tg_id)

        if len(msg.deadline) > 0:
            context.bot.send_message(chat_id=msg.user.tg_id,
                                     text=f"К {dt.datetime.strftime(msg.deadline[0].time, '%d.%m.%y %H:%M')}")


def handle_msg(update: Update, context: CallbackContext) -> str:
    adr_gr: Set[Group] = context.user_data["adr_groups"]
    message_id: int = update.message.message_id
    keywords: Set[str] = context.user_data['keywords']
    msg = Message(user=context.user_data["user"],
                  groups=list(adr_gr),
                  tg_id=message_id,
                  time=dt.datetime.now())

    with thread_local_session() as session:
        add_to_database([msg], session)
        msg.save_keywords(keywords)

    if "is_deadline" not in context.user_data.keys():
        with thread_local_session() as session:
            if not add_to_database([msg], session):
                context.bot.send_message(chat_id=msg.user.tg_id, text="Внутренняя ошибка в роботе.")
                raise RuntimeError("Failed to add deadline to db")

            send(context, msg)

        return ConversationHandler.END
    else:
        context.user_data["message"] = msg
        del context.user_data["user"]
        del context.user_data["keywords"]
        del context.user_data["adr_groups"]
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Введите время, к которому это надо сделать."
                                      "ДД.ММ.ГГ ЧЧ:ММ.")
        return "HANDLE_DUE_TIME"


def handle_due_time(update: Update, context: CallbackContext) -> str:
    text = update.message.text
    try:
        due_to = dt.datetime.strptime(text, "%d.%m.%y %H:%M")
        print(due_to)
        msg: Message = context.user_data["message"]
        with thread_local_session() as session:
            deadline = Deadline(msg=context.user_data["message"], time=due_to)
            if not add_to_database([msg, deadline], session):
                context.bot.send_message(chat_id=update.effective_chat.id, text="Внутренняя ошибка в роботе.")
                raise RuntimeError("Failed to add deadline to db")
            else:
                msg.deadline = [deadline]
                send(context, msg)

        return ConversationHandler.END
    except Exception as e:
        print(e)
        context.bot.send_message(chat_id=update.effective_chat.id, text="Неверный формат даты/времени. "
                                                                        "Попробуйте ещё")
        return "HANDLE_DUE_TIME"


def deadline_entry(update: Update, context: CallbackContext) -> str:
    context.user_data["is_deadline"] = True
    return send_entry(update, context)


def cancel(update: Update, context: CallbackContext) -> str:
    resp = "Вы отменили отправку сообщения." \
        if "is_deadline" in context.user_data \
        else "Вы отменили создание дедлайна"
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=resp
    )

    return ConversationHandler.END


send_conv = ConversationHandler(entry_points=[CommandHandler("send", send_entry)],
                                states={
                                    "HANDLE_KEYWORDS": [MessageHandler(Filters.text & (~Filters.command),
                                                                       handle_keywords)],
                                    "HANDLE_MSG_BODY": [MessageHandler(Filters.all,
                                                                       handle_msg)]},
                                fallbacks=[CommandHandler("cancel", cancel)])
dispatcher.add_handler(send_conv)

dead_conv = ConversationHandler(entry_points=[CommandHandler("deadline", deadline_entry)],
                                states={
                                    "HANDLE_KEYWORDS": [MessageHandler(Filters.text & (~Filters.command),
                                                                       handle_keywords)],
                                    "HANDLE_MSG_BODY": [MessageHandler(Filters.all,
                                                                       handle_msg)],
                                    "HANDLE_DUE_TIME": [MessageHandler(Filters.text & (~Filters.command),
                                                                       handle_due_time)]},
                                fallbacks=[CommandHandler("cancel", cancel)])

dispatcher.add_handler(dead_conv)
