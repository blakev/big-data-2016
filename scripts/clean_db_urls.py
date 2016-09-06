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

import sys

from logbook import Logger, StreamHandler

from vivint.db.core import connect, session_factory
from vivint.db.models import School

StreamHandler(sys.stdout).push_application()
logger = Logger(__name__)


# process constants
CONN_STRING = 'sqlite:///./data/school-data.original.db'

# setup the database
engine = connect(CONN_STRING, echo=True, pool_recycle=3600)
get_session = session_factory(engine)

session = get_session()

# selects all the rows with `WWW.DOMAIN` pattern and fixes them with `http://`
for row in session.query(School).filter(~School.url.like('http%')):
    row.url = 'http://' + row.url.lower()
    session.commit()

session.close()