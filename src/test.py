from database import session, User, Event
from datetime import datetime, timedelta
import random
import time
import logging
import os

logger = logging.getLogger()
logger.setLevel(level=os.environ.get("LOGLEVEL", "ERROR").upper())


def test_db():
    u = User(telegram_id=str(int(time.time())))
    print(u)

    session.add(u)
    for _ in range(7):
        e = Event(date=datetime.now() + timedelta(milliseconds=random.randint(1, 1000)))
        session.add(e)
        u.events.append(e)
    session.commit()

    print(*Event.upcoming_events(session, 2), sep="\n")


test_db()
time.sleep(2)  #  wait for scheduler to do jobs
