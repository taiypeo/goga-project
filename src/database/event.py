import enum
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

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, nullable=False, primary_key=True)
    recipient_id = Column(Integer, ForeignKey('users.id'))
    recipient = relationship("User", back_populates="events")
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
        return f'<Event user={self.recipient} date={self.date}{expired_str}>'
