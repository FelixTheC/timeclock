#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import uuid

from sqlalchemy import Column, DateTime, String, Integer, ForeignKey, func, Float, UniqueConstraint, \
    Boolean, Index
from tornado_sqlalchemy import declarative_base

from src.utils import working_time_repr

Base = declarative_base()
HOUR = 3600


def uuid_str():
    return str(uuid.uuid4())


class Employee(Base):
    __tablename__ = 'employee'
    id = Column(String, primary_key=True, default=uuid_str)
    uid = Column(String)
    name = Column(String)
    active = Column(Boolean, nullable=True, default=True)
    UniqueConstraint('uid', 'name', name='unique_uid_name_1')


class RCAuthentication(Base):
    __tablename__ = 'rcauthentication'
    id = Column(String, primary_key=True, default=uuid_str)
    uid = Column(String)
    requested_at = Column(DateTime, default=datetime.datetime.utcnow)
    authenticated_at = Column(DateTime, nullable=True)
    success = Column(Boolean, default=False)
    UniqueConstraint('uid', name='rcauthentication_uid_uindex')

    @property
    def out_of_time(self):
        return (datetime.datetime.utcnow() - self.requested_at).total_seconds() > 60


class TimeClock(Base):
    __tablename__ = 'timeclock'
    id = Column(String, primary_key=True, default=uuid_str)
    check_in = Column(DateTime)
    check_out = Column(DateTime, nullable=True)
    total = Column(Float, nullable=True)
    employee_id = Column(Integer, ForeignKey("employee.id"))

    def calculate_total_time(self):
        if self.check_out is not None:
            total = self.check_out - self.check_in
            self.total = total.total_seconds() / HOUR
        else:
            total = self.check_in - (self.check_in - datetime.timedelta(hours=0))
            self.total = total.total_seconds() / HOUR

    def to_dict(self):
        return {
            "id": self.id,
            "check_in": str(self.check_in),
            "check_out": str(self.check_out),
            "total": working_time_repr(self.total),
            "employee_id": self.employee_id,
        }

    def __repr__(self):
        return (f"{self.check_in} - {self.check_out} = {working_time_repr(self.total)}\n"
                f"{self.employee_id}")


indexes = [
    Index('idx_requested_at_desc', RCAuthentication.requested_at),
    Index('idx_authenticated_at_desc', RCAuthentication.authenticated_at),
    Index('idx_time_clock_check_in_desc', TimeClock.check_in),
    Index('idx_time_clock_check_out_desc', TimeClock.check_out),
]


def migrate():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.runserver import DATABASE_URL
    engine = create_engine('sqlite:////home/eisenmenger/PycharmProjects/time_clock/db.sqlite3')

    session = sessionmaker()
    session.configure(bind=engine)
    Base.metadata.create_all(engine)
    [idx.create(engine) for idx in indexes]
