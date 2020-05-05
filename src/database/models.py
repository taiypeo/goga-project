from . import Base, serializer
from .utils import add_to_database
from .permissions import SaIntFlagType, Perm
from typing import Set, List
from sqlalchemy import Column, Integer, Text, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.types import ARRAY
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm.session import Session as SessionGetter
from base64 import b64decode, b64encode
from binascii import Error as Base64DecodeError
from itsdangerous import BadSignature
from functools import reduce

msg_group = Table("messages_groups_match", Base.metadata,
                  Column("messages_id", Integer, ForeignKey("messages.id")),
                  Column("groups_id", Integer, ForeignKey("groups.id")))

msg_keyword = Table("messages_keywords_match", Base.metadata,
                    Column("messages_id", Integer, ForeignKey("messages.id")),
                    Column("keywords_id", Integer, ForeignKey("keywords.id")))


class PermissionError(RuntimeError):
    pass


class AlreadyJoinedError(RuntimeError):
    pass


class NonexistantGroup(RuntimeError):
    pass


class BadInvitation(RuntimeError):
    pass


class Permission(Base):
    __tablename__ = "permissions"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id"), primary_key=True)

    group = relationship("Group", back_populates="users")
    user = relationship("User", back_populates="groups")

    perm = Column(SaIntFlagType(Perm), default=0)

    def __repr__(self) -> str:
        return f"<Permission {self.user} {self.group}>"


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)

    users = relationship("Permission", back_populates="group")

    messages = relationship("Message", secondary="messages_groups_match")

    def __repr__(self) -> str:
        return f"<Group {self.title} users: {len(self.users)}>"


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)

    user = relationship("User")
    user_id = Column(Integer, ForeignKey("users.id"))

    groups = relationship("Group", secondary="messages_groups_match")

    tg_id = Column(Integer)
    time = Column(DateTime)

    deadline = relationship("Deadline", back_populates="msg")

    keywords = relationship("Keyword", secondary="messages_keywords_match")

    def save_keywords(self, words: Set[str]):
        session = SessionGetter.object_session(self)

        def get_obj(word: str) -> List[Keyword]:
            return session.query(Keyword).filter_by(word=word).all()

        lists: List[List[Keyword]] = list(map(get_obj, words))
        old = reduce(lambda x, y: x+y, lists)
        old_words = set(map(lambda x: x.word, old))
        new_words = words - old_words
        new = list(map(lambda x: Keyword(word=x, messages=[self]), new_words))
        print(f"old were {old_words} adding {new_words}")
        add_to_database(list(new), session)

        self.keywords = old+new

    def __repr__(self) -> str:
        ret = f"<Message {self.tg_id}."
        if self.deadline is not None:
            ret += f"Due to {self.deadline.time.isoformat()}."

        return ret + ">"


class Deadline(Base):
    __tablename__ = "deadlines"
    id = Column(Integer, primary_key=True)
    msg = relationship("Message", back_populates="deadline")
    msg_id = Column(Integer, ForeignKey("messages.id"))
    time = Column(DateTime)

    def __repr__(self):
        return f"<From {self.msg.user.tg_id} due to {self.time.isoformat()}>"


class Keyword(Base):
    __tablename__ = "keywords"
    id = Column(Integer, primary_key=True)
    word = Column(Text, unique=True)

    messages = relationship("Message", secondary="messages_keywords_match")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, nullable=False, unique=True)

    groups = relationship("Permission", back_populates="user")

    def __repr__(self):
        return f"<User tg: {self.tg_id}>"

    def create_invitation(self, invitee_permissions: Perm, group: Group) -> str:
        session = SessionGetter.object_session(self)
        permissions = session.query(Permission).get(
            {"user_id": self.id, "group_id": group.id}
        )

        if permissions is None:
            raise ValueError("User-group permission does not exist")

        if (
            invitee_permissions & Perm.post
            and not permissions.perm & Perm.invite_posters
        ):
            raise PermissionError("This user is not allowed to invite posters")
        if (
            not invitee_permissions & Perm.post
            and not permissions.perm & Perm.invite_students
        ):
            raise PermissionError("This user is not allowed to invite students")

        return b64encode(
            serializer.dumps(
                {"group_id": group.id, "permissions": invitee_permissions,}
            ).encode("utf-8")
        ).decode("utf-8")

    def accept_invite(self, invitation: str):
        """
        Raises BadInvitation and MultipleResultsFound (SQLAlchemy)
        """
        try:
            user_info = serializer.loads(
                b64decode(invitation.encode("utf-8")).decode("utf-8")
            )
        except (BadSignature, Base64DecodeError, UnicodeDecodeError):
            raise BadInvitation()

        if (
            not isinstance(user_info, dict)
            or "group_id" not in user_info
            or type(user_info["group_id"]) != int
        ):
            raise RuntimeError(
                "Invalid invitation payload: 'group_id' is not an 'int' or does not exist"
            )

        session = SessionGetter.object_session(self)
        group = session.query(Group).get(user_info["group_id"])
        if group is None:
            raise NonexistantGroup("Group does not exist")

        if "permissions" not in user_info or not isinstance(
            user_info["permissions"], int
        ):
            raise RuntimeError(
                (
                    "Invalid invitation payload: 'permissions' is not an instance of "
                    "'Perm' or does not exist"
                )
            )

        permissions = session.query(Permission).get(
            {"user_id": self.id, "group_id": group.id}
        )
        if permissions is not None:
            raise AlreadyJoinedError("User has already joined this group")

        permission = Permission(
            group=group, user=self, perm=Perm(user_info["permissions"])
        )

        if not add_to_database([permission], session):
            raise RuntimeError("Failed to add the permission to the database")

        return group


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    body = Column(Text, nullable=False)

    # users = relationship("User", back_populates="group")

    def __repr__(self) -> str:
        return f"<Notification {self.id} users: {len(self.users)}>"
