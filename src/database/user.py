from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from . import Base
from . import user_to_event
from .permissions import BindedPermissions

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, nullable=False, primary_key=True)
    telegram_id = Column(Integer, nullable=False)

    permissions_bits = Column(Integer, default=0)

    @property
    def permissions(self):
        return BindedPermissions(self, 'permissions_bits')

    events = relationship("Event", secondary=user_to_event, back_populates="users")

    course_id = Column(Integer, ForeignKey("courses.id"))
    course = relationship("Course", back_populates="users")

    def __repr__(self):
        capabilities = list()
        if self.can_post:
            capabilities.append("post")
        if self.can_invite_admins:
            capabilities.append("invite admins")
        if self.can_invite_posters:
            capabilities.append("invite posters")
        if self.can_invite_students:
            capabilities.append("invite students")
        if len(capabilities) > 0:
            capabilities = [""] + capabilities

        return f"<User tg_id={self.telegram_id}{' '.join(capabilities)}>"
