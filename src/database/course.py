from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship, backref

from . import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, nullable=False, primary_key=True)
    title = Column(Text, nullable=False)

    users = relationship("User", back_populates="course")
    tokens = relationship("Token", back_populates="course")

    parent_id = Column(Integer, ForeignKey("courses.id"))
    subcourses = relationship("Course", backref=backref("parent", remote_side=[id]))

    def __repr__(self):
        return f"<Course title={self.title}>"
