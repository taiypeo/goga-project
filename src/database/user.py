from sqlalchemy import Column, Integer, Boolean
from sqlalchemy.orm import relationship

from . import Base
from .many_to_many import course_to_user,user_to_event

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, nullable=False, primary_key=True)
    telegram_id = Column(Integer, nullable=False)

    can_post = Column(Boolean, nullable=False, default=False)
    can_create_subgroups = Column(Boolean, nullable=False, default=False)
    can_invite_admins = Column(Boolean, nullable=False, default=False)
    can_invite_posters = Column(Boolean, nullable=False, default=False)
    can_invite_students = Column(Boolean, nullable=False, default=False)

    events = relationship('Event', secondary=user_to_event, back_populates="users")
    courses = relationship("Course", secondary=course_to_user, back_populates="users")

    def __repr__(self):
        capabilities = list()
        if self.can_post: capabilities.append("post")
        if self.can_invite_admins: capabilities.append("invite admins")
        if self.can_invite_posters: capabilities.append("invite posters")
        if self.can_invite_students: capabilities.append("invite students")
        if len(capabilities) > 0:
            capabilities = [""] + capabilities

        return f"<User tg_id={self.telegram_id}{' '.join(capabilities)}>"
