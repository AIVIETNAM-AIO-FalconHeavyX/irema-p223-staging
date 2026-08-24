"""Declarative SQLAlchemy base shared by runtime and migrations."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
