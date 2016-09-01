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

import json

from logbook import Logger
import sqlalchemy.types as sqltypes

logger = Logger(__name__)


class Json(sqltypes.TypeDecorator):
    """ Converts a column to a JSON-object string on the way in,
        and a Python-dict on the way out.
    """

    impl = sqltypes.String

    def process_bind_param(self, value, dialect):
        if not isinstance(value, dict):
            raise ValueError(value)
        return json.dumps(value, sort_keys=True, indent=0)

    def process_result_value(self, value, dialect):
        return json.loads(value)


class TagList(sqltypes.TypeDecorator):
    """ Converts a column to a semi colon delimited string on the way in,
        and a Python-list on the way out.
    """

    impl = sqltypes.String

    def process_bind_param(self, value, dialect):
        value = value or ''
        return value.split(';')

    def process_result_value(self, value, dialect):
        if not hasattr(value, '__iter__'):
            raise ValueError(value)
        return ';'.join(map(str, value))
