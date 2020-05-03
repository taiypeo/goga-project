from sqlalchemy import (
    Column,
    Integer,
    SmallInteger,
    text,
    ForeignKey,
    DateTime,
    Boolean
)
from sqlalchemy.orm import relationship
from datetime import datetime

from . import Base
from .many_to_many import user_to_event

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, nullable=False, primary_key=True)
    users = relationship("User", secondary=user_to_event, back_populates="events")
    date = Column(DateTime, default=datetime.now)
    expired = Column(Boolean, default=False)

    @staticmethod
    def upcoming_events(session, limit: int=1):
        return (
            session
                .query(Event)
                .filter(Event.expired == False)
                .order_by(Event.date.asc())
                .limit(limit)
                .all()
        )

    def __repr__(self):
        expired_str = ' expired' if self.expired else ''
        user_count = len(self.users)
        if user_count != 1:
            return f'<Event users: {user_count} date={self.date}{expired_str}>'
        else:
            return f'<Event to: {self.users[0]} date={self.date}{expired_str}>'
            
