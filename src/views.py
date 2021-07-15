#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import json
import os
from datetime import date
from typing import Awaitable, Optional

import tornado.web
from sqlalchemy import and_, func, select
from tornado.escape import json_decode

from src.models import HOUR, Employee, RCAuthentication, TimeClock
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
        return self.application.settings["sqla"]()

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        return super().data_received(chunk)


class MainHandler(BaseRequestHandler):
    SUPPORTED_METHODS = ("GET",)

    async def get(self):
        await self.render("index.html")


class ListEmployeesRequest(BaseRequestHandler):
    SUPPORTED_METHODS = ["GET"]

    async def get(self):
        result = await self.sqla_session.execute(
            select(Employee).filter(Employee.active == True)
        )
        employees = [row["Employee"] for row in result.fetchall()]
        await self.render("list_employees.html", employees=employees)


async def database_stuff(user_uid, session):
    result = await session.execute(select(Employee).filter(Employee.uid == user_uid))
    employee = result.scalars().first()

    if employee is not None:
        result = await session.execute(
            select(RCAuthentication)
            .filter(
                and_(
                    RCAuthentication.uid == user_uid,
                    RCAuthentication.authenticated_at == None,
                    RCAuthentication.deleted == False,
                )
            )
            .order_by(RCAuthentication.requested_at.desc())
        )
        auth = result.scalars().first()
        if auth is not None:
            if not auth.out_of_time:
                if (
                    datetime.datetime.utcnow() - auth.requested_at
                ).total_seconds() > 600:
                    auth.success = False
                else:
                    auth.authenticated_at = datetime.datetime.utcnow()
                    auth.success = True
                await session.commit()
                return

        result = await session.execute(
            select(TimeClock)
            .join(Employee)
            .filter(
                and_(
                    Employee.uid == user_uid,
                    func.DATE(TimeClock.check_in) == date.today(),
                    TimeClock.check_out == None,
                )
            )
            .order_by(TimeClock.check_in.desc())
        )
        time_clock = result.scalars().first()
        if time_clock is None:
            tc = TimeClock(check_in=datetime.datetime.utcnow(), employee_id=employee.id)
            session.add_all(
                [
                    tc,
                ]
            )
            employee.checked_in = True
            await session.commit()
        else:
            time_clock.check_out = datetime.datetime.utcnow()
            time_clock.calculate_total_time()
            employee.checked_in = False
            await session.commit()
    return True


class CreateAuthRequest(BaseRequestHandler):
    SUPPORTED_METHODS = ("GET", "POST")

    async def get(self, user_uid):
        await self.render("authenticate.html", user_uid=user_uid)

    async def post(self, user_uid):
        tc = RCAuthentication(uid=user_uid)
        self.sqla_session.add_all(
            [
                tc,
            ]
        )
        await self.sqla_session.commit()

        counter = 0
        progress_bar = (
            f'<div id="pb" class="progress-bar progress-bar-striped" '
            f'style="width: {counter}%" '
            f'aria-valuenow="{counter}" aria-valuemin="0" aria-valuemax="60">'
            f"</div>"
        )

        await self.render(
            "proving_auth.html",
            auth_request_id=tc.id,
            counter=counter,
            progress_bar=progress_bar,
        )


class ValidateAuthRequest(BaseRequestHandler):
    SUPPORTED_METHODS = ("GET",)

    async def get(self, auth_id, counter):
        result = await self.sqla_session.execute(
            select(RCAuthentication).filter(
                and_(
                    RCAuthentication.id == auth_id,
                    RCAuthentication.authenticated_at != None,
                )
            )
        )
        auth = result.scalars().first()

        if auth is not None:
            self.redirect(f"/info/{auth.uid}")
        elif int(counter) == 60:
            result = await self.sqla_session.execute(
                select(RCAuthentication).filter(RCAuthentication.id == auth_id)
            )
            auth = result.scalars().first()
            auth.deleted = True
            await self.sqla_session.commit()
            self.write("<p>Authentication failed.</p>")
        else:
            progress_bar = (
                f'<div id="pb" class="progress-bar progress-bar-striped" '
                f'style="width: {counter}%" '
                f'aria-valuenow="{counter}" aria-valuemin="0" aria-valuemax="60">'
                f"</div>"
            )

            await self.render(
                "proving_auth.html",
                auth_request_id=auth_id,
                counter=int(counter) + 1,
                progress_bar=progress_bar,
            )


class NewEntry(BaseRequestHandler):
    """Only allow POST requests."""

    SUPPORTED_METHODS = ("POST",)

    async def post(self, user_uid):
        await database_stuff(user_uid, self.sqla_session)
        self.set_status(status_code=202)


class ListTimes(BaseRequestHandler):
    """Only allow GET requests."""

    SUPPORTED_METHODS = ("GET",)

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

    SUPPORTED_METHODS = ("GET",)

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
                    and_(
                        Employee.uid == user_uid,
                        func.DATE(TimeClock.check_in) == date.today(),
                    )
                )
                .order_by(TimeClock.check_in.asc())
            )
            data = result.fetchall()
            return_data = {"starting_time": "-", "breaks": [], "overall_total": "-"}
            if data:
                breaks = []
                for idx, _ in enumerate(data):
                    row = data[idx]
                    if row["TimeClock"].check_out is not None:
                        breaks.append({"start": row["TimeClock"].check_out})
                    if idx > 0:
                        selected_element = breaks[idx - 1]
                        selected_element["end"] = row["TimeClock"].check_in
                        selected_element["total"] = working_time_repr(
                            (
                                selected_element["end"] - selected_element["start"]
                            ).total_seconds()
                            / HOUR
                        )

                for row in data:
                    tt = row["TimeClock"].total
                    if tt is not None:
                        total_time += tt
                    else:
                        total_time += (
                            datetime.datetime.utcnow() - row["TimeClock"].check_in
                        ).total_seconds() / HOUR
                return_data = {
                    "starting_time": data[0]["TimeClock"].check_in,
                    "breaks": breaks,
                    "overall_total": working_time_repr(total_time),
                }
            await self.render("info.html", **return_data)
        else:
            self.send_error(status_code=404)


class CreateNewEmployeeRequest(BaseRequestHandler):
    SUPPORTED_METHODS = ("POST",)

    async def post(self, verfication_str):
        if verfication_str == os.getenv("SECRET"):
            self.args = json_decode(self.request.body)
            user_id = self.args["user_id"]
            user_name = self.args["username"]
            new_user = Employee(uid=user_id, name=user_name)
            self.sqla_session.add_all(
                [
                    new_user,
                ]
            )
            await self.sqla_session.commit()
            self.set_status(201)
        else:
            self.send_error(403)
