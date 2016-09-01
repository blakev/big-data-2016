#! /usr/bin/env python
# -*- coding: utf-8 -*-
# >>
#     Copyright (c) 2016, Blake VandeMerwe - Vivint, inc.
#
#       Permission is hereby granted, free of charge, to any person obtaining
#       a copy of this software and associated documentation files
#       (the "Software"), to deal in the Software without restriction,
#       including without limitation the rights to use, copy, modify, merge,
#       publish, distribute, sublicense, and/or sell copies of the Software,
#       and to permit persons to whom the Software is furnished to do so, subject
#       to the following conditions: The above copyright notice and this permission
#       notice shall be included in all copies or substantial portions
#       of the Software.
#
#     big-data-2016, 2016
# <<

from logbook import Logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from vivint.db.models import Base

logger = Logger(__name__)


def connect(connection_string: str, **kwargs):
    engine = create_engine(connection_string, **kwargs)
    return engine


def create_tables(engine) -> None:
    Base.metadata.create_all(engine)


def session_factory(engine):
    def wrapped():
        return session()
    session = sessionmaker(bind=engine)
    return wrapped
