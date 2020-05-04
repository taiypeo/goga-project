from typing import Tuple, List
import itertools

from sqlalchemy.exc import DatabaseError
from . import session, User, Course, Token


def add_to_database(obj) -> bool:
    try:
        session.add(obj)
        session.commit()
    except DatabaseError:
        session.rollback()
        return False

    return True


def get_users(tg_id: int):
    return session.query(User).filter_by(telegram_id=id).all()

def check_permissions(
    tg_id: int, course_name: str, permissions: Tuple[int, int, int, int, int],
) -> bool:
    course = session.Query(Course).filter_by(title=course_name).first()
    if course is None:
        return False

    user = next((u for u in course.users if u.telegram_id == tg_id), None)
    if user is None:
        return False

    valid = True
    user_perms = [
        user.can_post,
        user.can_create_subgroups,
        user.can_invite_admins,
        user.can_invite_posters,
        user.can_invite_students,
    ]
    for i in range(len(permissions)):
        if permissions[i] is not None:
            valid = valid and user_perms[i] == permissions[i]

    return valid


def add_permission(
    tg_id: int, course_name: str, permissions: Tuple[int, int, int, int, int]
) -> bool:
    course: Course = session.query(Course).filter_by(title=course_name).first()
    if course is None:
        return False

    user = next((u for u in course.users if u.telegram_id == tg_id), None)
    if user is None:
        user = User(telegram_id=tg_id)

    user.can_post = permissions[0]
    user.can_create_subgroups = permissions[1]
    user.can_invite_admins = permissions[2]
    user.can_invite_posters = permissions[3]
    user.can_invite_students = permissions[4]

    return add_to_database(user)


def add_token(
    token: str, course_name: str, permissions
) -> bool:
    course_exists = session.query(Course).filter_by(title=course_name).count() > 0
    if not course_exists:
        add_to_database(Course(title=course_name))

    course = session.query(Course).filter_by(title=course_name).one()

    found = session.query(Token).filter_by(token=token).first()
    if found is not None:
        return False

    token = Token(token=token, course=course)
    token.permissions.enable_from(permissions)

    return add_to_database(token)


def check_token_presence(token: str) -> bool:
    return session.query(Token).filter_by(token=token).count() > 0
