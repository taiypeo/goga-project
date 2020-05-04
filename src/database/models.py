from . import Base, serializer
from .utils import add_to_database
from .permissions import SaIntFlagType, Perm

from sqlalchemy import Column, Integer, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm.session import Session as SessionGetter
from base64 import b64decode, b64encode
from binascii import Error as Base64DecodeError
from itsdangerous import BadSignature


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

    def __repr__(self) -> str:
        return f"<Group {self.title} users: {len(self.users)}>"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, nullable=False, unique=True)

    groups = relationship("Permission", back_populates="user")

    def __repr__(self):
        return f"<User tg: {self.tg_id}>"

    def create_invitation(self, invitee_permissions: Perm, group: Group) -> str:
        session = SessionGetter.object_session(self)
        permissions = (
            session.query(Permission)
            .get({"user_id": self.id, "group_id": group.id})
        )

        if permissions is None:
            raise ValueError("User-group permission does not exist")

        if invitee_permissions & Perm.post and not permissions.perm & Perm.invite_posters:
            raise PermissionError("This user is not allowed to invite posters")
        if (
            not invitee_permissions & Perm.post
            and not permissions.perm & Perm.invite_students
        ):
            raise PermissionError("This user is not allowed to invite students")

        return b64encode(serializer.dumps(
            {"group_id": group.id, "permissions": invitee_permissions,}
        ).encode('utf-8')).decode('utf-8')

    def accept_invite(self, invitation: str):
        """
        Raises BadInvitation and MultipleResultsFound (SQLAlchemy)
        """
        try:
            user_info = serializer.loads(b64decode(invitation.encode('utf-8')).decode('utf-8'))
        except (BadSignature, Base64DecodeError, UnicodeDecodeError):
            raise BadInvitation()

        if not isinstance(user_info, dict) or "group_id" not in user_info or type(user_info["group_id"]) != int:
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

        permission = Permission(group=group, user=self, perm=Perm(user_info["permissions"]))

        if not add_to_database([permission], session):
            raise RuntimeError("Failed to add the permission to the database")

        return group


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    body = Column(Text, nullable=False)

    #users = relationship("User", back_populates="group")

    def __repr__(self) -> str:
        return f"<Notification {self.id} users: {len(self.users)}>"
