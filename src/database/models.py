from . import Base, serializer
from .permissions import SaIntFlagType, Perm

from sqlalchemy import Column, Integer, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm.session import Session as SessionGetter


class PermissionError(RuntimeError):
    pass


def _add_to_database(obj: object, session) -> bool:
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
            .one()
        )

        if invitee_permissions & Perm.post and not permissions & Perm.invite_posters:
            raise PermissionError("This user is not allowed to invite posters")
        if (
            not invitee_permissions & Perm.post
            and not permissions & Perm.invite_students
        ):
            raise PermissionError("This user is not allowed to invite students")

        return serializer.dumps(
            {"group_id": group.id, "permissions": invitee_permissions,}
        )

    def accept_invite(self, invitation: str):
        """
        Raises BadSignature (itsdangerous) and MultipleResultsFound (SQLAlchemy)
        """

        user_info = serializer.loads(invitation)

        if "group_id" not in user_info or type(user_info["group_id"]) != int:
            raise RuntimeError(
                "Invalid invitation payload: 'group_id' is not an 'int'\
                    or does not exist"
            )

        session = SessionGetter.object_session(self)
        group = session.Query(Group).get(user_info["group_id"]).one()

        if "permissions" not in user_info or not isinstance(
            user_info["permissions"], Perm
        ):
            raise RuntimeError(
                "Invalid invitation payload: 'permissions' is not\
                    an instance of 'BindedPermissions' or does\
                    not exist"
            )

        permission = Permission(group=group, user=self, perm=user_info["permissions"])

        if not _add_to_database(permission, session):
            raise RuntimeError("Failed to add the permission to the database")
