from datetime import date, datetime

from sqlalchemy import ForeignKey, text, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from uuid import UUID
from uuid import uuid4


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    user_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(unique=True)
    username: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str]
    birthdate: Mapped[date]
    phone_number: Mapped[str] = mapped_column(unique=True)
    files: Mapped[list["File"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return self.email


class File(Base):
    __tablename__ = "file"

    file_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    filename: Mapped[str]
    size: Mapped[int] = mapped_column(BigInteger, default=0)
    uploaded_at:  Mapped[datetime] = mapped_column(server_default=text("TIMEZONE ('utc', now())"))
    file_path: Mapped[str] = mapped_column(unique=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.user_id"))
    user: Mapped["User"] = relationship(back_populates="files")

    def __repr__(self):
        return self.filename
