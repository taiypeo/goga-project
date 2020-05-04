from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

engine = create_engine("sqlite:///../db.sqlite")
# engine = create_engine("postgres://172.24.24.21")
Base = declarative_base()
Session = scoped_session(sessionmaker(bind=engine))

from .models import *

Base.metadata.create_all(engine)
session = Session()
