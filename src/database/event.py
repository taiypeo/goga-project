from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    Boolean,
)
from sqlalchemy.orm import relationship, scoped_session
from sqlalchemy.orm.session import Session as SessionModule
from sqlalchemy import event
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from . import Base, engine as alchemy_engine, Session
from .many_to_many import user_to_event
from logging import info, error
import threading

ScopedSessionMaker = scoped_session(Session)

sched = BackgroundScheduler(
    job_stores={"default": SQLAlchemyJobStore(engine=alchemy_engine)}
)

sched.start()


def execute_event(id):
    sess = ScopedSessionMaker()
    ev = sess.query(Event).filter_by(id=id).first()
    if ev is not None:
        ev.execute()
    else:
        error(f"event #{id} not found in db")
    ScopedSessionMaker.remove()


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, nullable=False, primary_key=True)
    users = relationship("User", secondary=user_to_event, back_populates="events")
    date = Column(DateTime, default=datetime.now)
    expired = Column(Boolean, default=False)

    @staticmethod
    def upcoming_events(session, limit: int = 1):
        return (
            session.query(Event)
            .filter(Event.expired == False)
            .order_by(Event.date.asc())
            .limit(limit)
            .all()
        )

    def execute(self):
        print(f"executing {self}")
        self.expired = True
        session = SessionModule.object_session(self)
        session.add(self)
        session.commit()

    def __repr__(self):
        expired_str = " expired" if self.expired else ""
        user_count = len(self.users)
        if user_count != 1:
            return (
                f"<Event #{self.id} users: {user_count} date={self.date}{expired_str}>"
            )
        else:
            return (
                f"<Event #{self.id} to: {self.users[0]} date={self.date}{expired_str}>"
            )


@event.listens_for(Event, "after_insert")
def insert_in_sched(mapper, connection, target):
    sched.add_job(execute_event, "date", run_date=target.date, args=[target.id])
    info(f"Scheduled {target}")
