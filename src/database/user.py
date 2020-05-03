from sqlalchemy import Column, Integer, Boolean, text

from . import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, nullable=False, primary_key=True)
    telegram_id = Column(Integer, nullable=False)

    can_post = Column(Boolean, nullable=False, default=False)
    can_invite_admins = Column(Boolean, nullable=False, default=False)
    can_invite_posters = Column(Boolean, nullable=False, default=False)
    can_invite_students = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<User tg_id={self.telegram_id}\
            can_post={self.can_post}>\
            can_invite_admins={self.can_invite_admins}\
            can_invite_posters={self.can_invite_posters}\
            can_invite_students={self.can_invite_students}"
