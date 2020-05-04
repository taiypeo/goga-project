from ..config import secret_key

from . import Base, session
from .permissions import BindedPermissions

from sqlalchemy import Column, Integer, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.exc import DatabaseError
from itsdangerous.serializer import Serializer, BadSignature


def _add_to_database(obj: object) -> bool:
    try:
        session.add(obj)
        session.commit()
    except DatabaseError:
        session.rollback()
        return False

    return True


class Permission(Base):
    __tablename__ = "permissions"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id"), primary_key=True)

    permissions_bits = Column(Integer, default=0)

    group = relationship("Group", back_populates="users")
    user = relationship("User", back_populates="groups")

    @property
    def permissions(self):
        return BindedPermissions(self, "permissions_bits")


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)

    users = relationship("Permission", back_populates="group")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, nullable=False, unique=True)

    groups = relationship("Permission", back_populates="user")

    def create_invitation(
        self, invitee_tg_id: int, invitee_permissions: BindedPermissions, group: Group
    ) -> str:
        permissions = (
            session.query(Permission)
            .get({"user_id": self.id, "group_id": group.id})
            .first()
        )
        if permissions is None:
            raise ValueError("Invalid user-group pair for permissions")

        if invitee_permissions.is_enabled("post") and not permissions.is_enabled(
            "invite_posters"
        ):
            raise RuntimeError("This user is not allowed to invite posters")
        if not invitee_permissions.is_enabled("post") and not permissions.is_enabled(
            "invite_students"
        ):
            raise RuntimeError("This user is not allowed to invite students")

        serializer = Serializer(secret_key)
        return serializer.dumps(
            {
                "tg_id": invitee_tg_id,
                "group_id": group.id,
                "permissions": invitee_permissions,
            }
        )

    @staticmethod
    def invite(self, invitation: str) -> User:
        serializer = Serializer(secret_key)
        try:
            user_info = serializer.loads(invitation)
        except BadSignature:
            raise RuntimeError("Invalid signature for the invitation")

        if "tg_id" not in user_info or type(user_info["tg_id"]) != int:
            raise RuntimeError(
                "Invalid invitation payload: 'tg_id' is not an 'int'\
                    or does not exist"
            )

        user = User(tg_id=user_info["tg_id"])
        if not _add_to_database(user):
            raise RuntimeError("Failed to add the user to the database")

        if "group_id" not in user_info or type(user_info["group_id"]) != int:
            raise RuntimeError(
                "Invalid invitation payload: 'group_id' is not an 'int'\
                    or does not exist"
            )

        group = session.Query(Group).get(user_info["group_id"]).first()
        if group is None:
            raise RuntimeError("Group with this ID does not exist")

        if (
            "permissions" not in user_info
            or type(user_info["permissions"]) != BindedPermissions
        ):
            raise RuntimeError(
                "Invalid invitation payload: 'permissions' is not\
                    an instance of 'BindedPermissions' or does\
                    not exist"
            )

        permission = Permission(group=group, user=user)
        # TODO: set permission bits

        if not _add_to_database(permission):
            raise RuntimeError("Failed to add the permission to the database")

        return user
