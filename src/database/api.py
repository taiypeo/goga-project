from typing import Tuple, List
import itertools

from sqlalchemy.exc import DatabaseError
from . import session, User, Course


def add_to_database(obj) -> bool:
    try:
        session.add(obj)
        session.commit()
    except DatabaseError:
        session.rollback()
        return False

    return True


def permission_courses(
    tg_id: int, permissions: Tuple[int, int, int, int, int]
) -> List[Course]:
    query = session.query(User)
    perm_names = [
        "can_post",
        "can_create_subgroups",
        "can_invite_admins",
        "can_invite_posters",
        "can_invite_students",
    ]
    kwargs = {"telegram_id": tg_id}
    for i in range(permissions):
        if permissions[i] is not None:
            kwargs[perm_names[i]] = permissions[i]

    users = session.query(User).filter_by(**kwargs).all()
    return [u.course for u in users]


def add_user(
    tg_id: int, permissions: Tuple[int, int, int, int, int], course: Course
) -> bool:
    user = next((u for u in course.users if u.telegram_id == tg_id), None)
    if user is None:
        user = User(telegram_id=tg_id)

    user.can_post = permissions[0]
    user.can_create_subgroups = permissions[1]
    user.can_invite_admins = permissions[2]
    user.can_invite_posters = permissions[3]
    user.can_invite_students = permissions[4]

    return add_to_database(user)
