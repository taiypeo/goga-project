from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

engine = create_engine("sqlite:///../db.sqlite")
#engine = create_engine("postgres://172.24.24.21")
Base = declarative_base()
Session = scoped_session(sessionmaker(bind=engine))

from .token import *
from .event import *
from .user import *
from .course import *

Base.metadata.create_all(engine)

session = Session()

from .api import *
