#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def working_time_repr(total_time: float) -> str:
    if total_time is not None:
        hours = int(total_time)
        minutes = int(round(((total_time % 1) * .6) * 100, 1))
        return f"{hours} hours {minutes} minutes"
