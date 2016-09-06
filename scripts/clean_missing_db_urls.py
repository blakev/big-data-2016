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

import time
import random
import sys
import signal
import multiprocessing as mp

from logbook import Logger, StreamHandler
from selenium.webdriver import Firefox

from vivint.db.core import connect, session_factory
from vivint.db.models import School
from vivint.grab.ratemyprof import get_driver

StreamHandler(sys.stdout).push_application()
logger = Logger(__name__)


# process constants
MAX_WORKERS = 15
TIMEOUT_SECS = 15
CONN_STRING = 'sqlite:///../data/school-data.db'
SEARCH_URL = 'https://duckduckgo.com/?q={query}&t=h_&ia=web'

# setup the database
engine = connect(CONN_STRING, echo=True, pool_recycle=3600)
get_session = session_factory(engine)

session = get_session()


def find_school_url(row):
    driver = Firefox()
    driver.implicitly_wait(10.0)

    if driver is None:
        logger.error('SKIPPING ' + row.name)
        return

    boost_terms = [
        row.loc_state,
        'region:us',
        '-fafsa-application.com',
        '-webcrawler.com'
    ]

    url = SEARCH_URL.format(query='+'.join(row.name.split() + boost_terms))

    # do the google search
    driver.get(url)

    time.sleep(random.randint(2, 4))

    # look for the first url
    top_result = driver.find_element_by_css_selector('div.result')
    result_link = top_result.find_element_by_css_selector('div.result__extras__url')

    poss_url = '~http://' + result_link.text.strip(' ./')

    row.url = poss_url

    # close out of the driver
    driver.quit()
    session.add(row)
    session.commit()

    print(row.name, row.url)


with mp.Pool(processes=MAX_WORKERS) as pool:
    results = pool.map(find_school_url, session.query(School).filter(School.url.is_(None)))

session.close()