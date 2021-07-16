#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path

import tornado.web
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.locks import Event
from tornado.options import define, options
from tornado_sqlalchemy import SQLAlchemy

from src.template_functions import parse_date
from src.views import (
    CreateAuthRequest,
    CreateNewEmployeeRequest,
    InfoCurrentWorkingTime,
    ListEmployeesRequest,
    ListTimes,
    MainHandler,
    NewEntry,
    ValidateAuthRequest,
)

load_dotenv()

BASE_DIR = Path(__file__).parent
DATABASE_PATH = "/home/felix/PycharmProjects/timeclock/db.sqlite3"
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"
sqla_engine = create_async_engine(DATABASE_URL, echo=True)

define("port", default=8888, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self, db):
        handlers = [
            (r"/", MainHandler),
            (r"/list/employees", ListEmployeesRequest),
            (r"/auth/request/(.*)", CreateAuthRequest),
            (r"/validate/auth/(.*)", ValidateAuthRequest),
            (r"/new-employee/(.*)", CreateNewEmployeeRequest),
            (r"/add/(.*)", NewEntry),
            (r"/list/(.*)", ListTimes),
            (r"/info/(.*)", InfoCurrentWorkingTime),
        ]
        settings = dict(
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            template_path=str(BASE_DIR / Path("templates")),
            static_path=str(BASE_DIR / Path("static")),
            xsrf_cookies=False,
            # ui_modules={"Post": PostModule},
            debug=True,
            autoescape=None,
            db=db,
            sqla=sessionmaker(sqla_engine, class_=AsyncSession, expire_on_commit=False),
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        self.ui_methods["parse_date"] = parse_date


async def main():
    """Construct and serve the tornado application."""
    tornado.options.parse_command_line()
    # for command line parameters
    # if not (options.facebook_api_key and options.facebook_secret):
    #     print("--facebook_api_key and --facebook_secret must be set")
    #     return
    http_server = tornado.httpserver.HTTPServer(Application(SQLAlchemy(DATABASE_URL)))
    http_server.listen(options.port)
    sys.stdout.write(f"Listening on http://localhost:{options.port}\n\n")

    shutdown_event = Event()
    await shutdown_event.wait()


if __name__ == "__main__":
    IOLoop.current().run_sync(main)
