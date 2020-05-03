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
    users = (
        session.query(User)
        .filter_by(
            telegram_id=tg_id,
            can_post=permissions[0],
            can_create_subgroups=permissions[1],
            can_invite_admins=permissions[2],
            can_invite_posters=permissions[3],
            can_invite_students=permissions[4],
        )
        .all()
    )

    return [u.course for u in users]
