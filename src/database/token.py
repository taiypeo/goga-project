from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, backref

from . import Base
from .permissions import BindedPermissions


class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, nullable=False, primary_key=True)
    token = Column(String(length=36), nullable=False, unique=True, index=True)

    permissions_bits = Column(Integer, default=0)

    @property
    def permissions(self):
        return BindedPermissions(self, 'permissions_bits')


    course_id = Column(Integer, ForeignKey("courses.id"))
    course = relationship("Course", back_populates="tokens")

    def __repr__(self):
        return f"<Course title={self.title}>"
