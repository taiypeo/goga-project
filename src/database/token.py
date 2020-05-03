from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, backref

from . import Base


class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, nullable=False, primary_key=True)
    token = Column(String(length=36), nullable=False, unique=True, index=True)

    can_post = Column(Boolean, nullable=False, default=False)
    can_create_subgroups = Column(Boolean, nullable=False, default=False)
    can_invite_admins = Column(Boolean, nullable=False, default=False)
    can_invite_posters = Column(Boolean, nullable=False, default=False)
    can_invite_students = Column(Boolean, nullable=False, default=False)

    course_id = Column(Integer, ForeignKey("courses.id"))
    course = relationship("Course", back_populates="tokens")

    def __repr__(self):
        return f"<Course title={self.title}>"
