def add_to_database(obj: object, session) -> bool:
    try:
        session.add(obj)
        session.commit()
    except DatabaseError:
        session.rollback()
        return False

    return True
