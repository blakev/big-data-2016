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

import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column, Integer, String, DateTime, Float,
    Boolean, Date, ForeignKey, ForeignKeyConstraint
)

from .types import Json


Base = declarative_base()


class School(Base):
    __tablename__ = 'school'

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    comments = relationship('SchoolComment', back_populates='school')
    teachers = relationship('Teacher', back_populates='school')

    name = Column(String(255), nullable=False)
    sid = Column(Integer, nullable=True)
    url = Column(String(255), nullable=True, default=None)
    loc_addr = Column(String(256), nullable=True, default=None)
    loc_city = Column(String(128), nullable=True, default=None)
    loc_state = Column(String(16), nullable=True, default=None)
    loc_zip = Column(String(16), nullable=True, default=None)
    scores = Column(Json(1024), nullable=True, default={})


class SchoolComment(Base):
    __tablename__ = 'school_comments'

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    school_id = Column(Integer, ForeignKey('school.id'))
    school = relationship('School')

    date_reviewed = Column(Date)
    text = Column(String(1024*16))

    clubs = Column(Float, default=0.0)
    facilities = Column(Float, default=0.0)
    food = Column(Float, default=0.0)
    happiness = Column(Float, default=0.0)
    internet = Column(Float, default=0.0)
    location = Column(Float, default=0.0)
    opportunities = Column(Float, default=0.0)
    reputation = Column(Float, default=0.0)
    safety = Column(Float, default=0.0)
    social = Column(Float, default=0.0)
    campus = Column(Float, default=0.0)
    library = Column(Float, default=0.0)
    graduation_year = Column(Integer, default=None, nullable=True)


class SchoolSocial(Base):
    __tablename__ = 'school_social'

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    school_id = Column(Integer, ForeignKey('school.id'))
    school = relationship('School')

    phone = Column(String(16), nullable=True, default=None)
    email = Column(String(255), nullable=True, default=None)
    facebook = Column(String(255), nullable=True, default=None)
    instagram = Column(String(255), nullable=True, default=None)
    pinterest = Column(String(255), nullable=True, default=None)
    google_plus = Column(String(255), nullable=True, default=None)
    twitter = Column(String(255), nullable=True, default=None)
    youtube = Column(String(255), nullable=True, default=None)


class Teacher(Base):
    __tablename__ = 'teachers'

    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    school_id = Column(Integer, ForeignKey('school.id'))
    school = relationship('School', back_populates='teachers')

    tid = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    is_top = Column(Boolean, default=False)
