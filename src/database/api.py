from sqlalchemy.exc import DatabaseError
from . import session


def add_to_database(obj) -> bool:
    try:
        session.add(obj)
        session.commit()
    except DatabaseError:
        session.rollback()
        return False

    return True
