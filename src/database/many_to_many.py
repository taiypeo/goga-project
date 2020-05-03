from sqlalchemy import Table, Column, Integer, ForeignKey
from . import Base

user_to_event = Table('user_to_event', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('event_id', Integer, ForeignKey('events.id'))
)
