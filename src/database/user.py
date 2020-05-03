import enum
from sqlalchemy import Column, Integer, SmallInteger, text

from . import Base


ROLE_ADMIN = 0
ROLE_INFO_SOURCE = 1
ROLE_STUDENT = 2


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, nullable=False, primary_key=True)
    telegram_id = Column(Integer, nullable=False, unique=True, index=True)
    role = Column(SmallInteger, default=ROLE_STUDENT, nullable=False)

    def __repr__(self):
        role_strs = ["ADMIN", "INFO_SOURCE", "STUDENT"]
        role_str = "UNKNOWN"
        if 0 <= self.role <= 2:
            role_str = role_strs[self.role]

        return f"<User tg_id={self.telegram_id} role={role_str}>"
