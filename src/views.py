#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import datetime
import json
import time
from datetime import date
from pprint import pprint
from typing import Optional, Awaitable

import tornado.web
from sqlalchemy import and_, func, select

from src.models import Employee, TimeClock, HOUR, RCAuthentication
from src.utils import working_time_repr


class BaseRequestHandler(tornado.web.RequestHandler):
    async def prepare(self):
        self.sqla_session = self.generate_sqla_session()

    def on_finish(self):
        """
        Since Tornado on_finish is not async by default,
        we run the on_finish_async inside the tornado loop.
        """
        io_loop = tornado.ioloop.IOLoop.current()
        io_loop.add_callback(self.on_finish_async)

    async def on_finish_async(self):
        try:
            if self.sqla_session:
                await self.sqla_session.close()
        except AttributeError:
            return True

    def generate_sqla_session(self):
        return self.application.settings['sqla']()

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        return super().data_received(chunk)


class MainHandler(BaseRequestHandler):
    SUPPORTED_METHODS = ["GET"]

    async def get(self):
        result = await self.sqla_session.execute(select(Employee).filter(Employee.active == True))
        employees = [row["Employee"] for row in result.fetchall()]
        await self.render("index.html", employees=employees)


async def database_stuff(user_uid, session):
    result = await session.execute(select(Employee).filter(Employee.uid == user_uid))
    employee = result.scalars().first()

    if employee is not None:
        result = await session.execute(
            select(RCAuthentication)
                .filter(and_(RCAuthentication.uid == user_uid,
                             RCAuthentication.authenticated_at == None))
                .order_by(RCAuthentication.requested_at.desc())
        )
        auth = result.scalars().first()
        if auth is not None:
            if not auth.out_of_time():
                if (datetime.datetime.utcnow() - auth.requested_at).total_seconds() > 600:
                    auth.success = False
                else:
                    auth.authenticated_at = datetime.datetime.utcnow()
                    auth.success = True
                await session.commit()
                return

        result = await session.execute(select(TimeClock).join(Employee).filter(
            and_(Employee.uid == user_uid,
                 func.DATE(TimeClock.check_in) == date.today(),
                 TimeClock.check_out == None)
        ).order_by(TimeClock.check_in.desc()))
        time_clock = result.scalars().first()
        if time_clock is None:
            tc = TimeClock(check_in=datetime.datetime.utcnow(), employee_id=employee.id)
            session.add_all([tc, ])
            await session.commit()
        else:
            time_clock.check_out = datetime.datetime.utcnow()
            time_clock.calculate_total_time()
            await session.commit()
    return True


class CreateAuthRequest(BaseRequestHandler):
    SUPPORTED_METHODS = ["GET"]

    async def get(self, user_uid):
        tc = RCAuthentication(uid=user_uid)
        self.sqla_session.add_all([tc, ])
        await self.sqla_session.commit()

        await self.render("authenticate.html", auth_request_id=tc.id)


class ValidateAuthRequest(BaseRequestHandler):
    SUPPORTED_METHODS = ["GET"]

    async def get(self, auth_id):
        auth = None
        for _ in range(60):
            result = await self.sqla_session.execute(
                select(RCAuthentication).filter(and_(RCAuthentication.id == auth_id,
                                                     RCAuthentication.authenticated_at != None
                                                     ))
            )
            auth = result.scalars().first()
            if auth is not None:
                break
            await asyncio.sleep(1)

        if auth is not None:
            self.redirect(f"/info/{auth.uid}")
        else:
            self.write("<p>Authentication failed.</p>")


class NewEntry(BaseRequestHandler):
    """Only allow POST requests."""
    SUPPORTED_METHODS = ["POST"]

    async def post(self, user_uid):
        await database_stuff(user_uid, self.sqla_session)
        self.set_status(status_code=202)


class ListTimes(BaseRequestHandler):
    """Only allow GET requests."""
    SUPPORTED_METHODS = ["GET"]

    async def get(self, user_uid):
        result = await self.sqla_session.execute(
            select(TimeClock)
                .join(Employee)
                .filter(Employee.uid == user_uid)
                .order_by(TimeClock.check_in.desc())
        )
        entities = result.fetchall()
        data = [entity["TimeClock"].to_dict() for entity in entities]
        self.write(json.dumps(data))


class InfoCurrentWorkingTime(BaseRequestHandler):
    """Only allow GET requests."""
    SUPPORTED_METHODS = ["GET"]

    async def get(self, user_uid):
        result = await self.sqla_session.execute(
            select(Employee).filter(Employee.uid == user_uid)
        )
        employee = result.scalars().first()
        if employee is not None:
            break_ = []
            total_time = 0
            result = await self.sqla_session.execute(
                select(TimeClock)
                    .join(Employee)
                    .filter(
                    and_(Employee.uid == user_uid,
                         func.DATE(TimeClock.check_in) == date.today()
                         ))
                    .order_by(TimeClock.check_in.asc())
            )
            data = result.fetchall()
            for idx, row in enumerate(data, 1):
                if idx % 2 == 0:
                    break_.append(row["TimeClock"].check_in)
                else:
                    checkout_time = row["TimeClock"].check_out
                    if checkout_time is not None:
                        break_.append(checkout_time)
                    else:
                        break

            for row in data:
                tt = row["TimeClock"].total
                if tt is not None:
                    total_time += tt
                else:
                    total_time += (datetime.datetime.utcnow() - row["TimeClock"].check_in
                                   ).total_seconds() / HOUR

            breaks_and_break_time = []
            for i in range(0, len(break_), 2):
                sub_split = break_[i: i+2]
                breaks_and_break_time.append({
                    "start": sub_split[0],
                    "end": sub_split[1],
                    "total": working_time_repr((sub_split[1] - sub_split[0]).total_seconds() / HOUR)
                })
            data = {
                "starting_time": data[0]["TimeClock"].check_in,
                "breaks": breaks_and_break_time,
                "overall_total": working_time_repr(total_time)
            }
            await self.render("info.html", **data)
        else:
            self.send_error(status_code=404)
