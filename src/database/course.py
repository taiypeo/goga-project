from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship
from . import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, nullable=False, primary_key=True)
