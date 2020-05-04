from typing import List
from sqlalchemy.exc import DatabaseError
from . import Session
from contextlib import contextmanager


@contextmanager
def thread_local_session():
    try:
        yield Session()
    finally:
        Session.remove()


def add_to_database(obj_list: List[object], session) -> bool:
    try:
        for obj in obj_list:
            session.add(obj)

        session.commit()
    except DatabaseError:
        session.rollback()
        return False

    return True
