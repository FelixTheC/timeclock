#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime

from tornado import template


def parse_date(view, data: datetime.datetime):
    try:
        return data.strftime("%Y-%m-%d %H:%M")
    except (AttributeError, ValueError):
        return data
