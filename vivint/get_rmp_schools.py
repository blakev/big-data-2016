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

import csv
import multiprocessing as mp
import random
import signal
import sys
import time
from collections import namedtuple
from http.client import HTTPException

from logbook import Logger, StreamHandler
from selenium.common.exceptions import NoSuchElementException

from vivint.db.core import connect, create_tables, session_factory
from vivint.db.models import School
from vivint.grab.ratemyprof import get_driver, get_school_id, get_school_comments

SchoolDetails = namedtuple('SchoolDetails', 'name city state zipcode url')

StreamHandler(sys.stdout).push_application()

logger = Logger(__name__)
school_list = list()

# process constants
WORKER_COUNT = 10
MAX_COMMENTS = 100
CONN_STRING = 'sqlite:////tmp/rmp-db.sqlite'

# setup0 the database
engine = connect(CONN_STRING, echo=True, pool_recycle=3600)
create_tables(engine)
get_session = session_factory(engine)


with open('/tmp/uni_names.csv') as csv_in:
    reader = csv.reader(csv_in, delimiter=',', quotechar='"')
    for row in reader:
        d = SchoolDetails(*row)
        school_list.append(d)


def get_school_id_worker(d):
    s_time = time.time()

    driver = get_driver()    # allocate a PhantomJS driver
    session = get_session()  # allocate a database session

    if driver is None:
        logger.error('SKIPPING ' + d.name)
        s = School(name=d.name)
        session.add(s)
        session.commit()
        session.close()
        return

    logger.info('Starting: ' + d.name)

    time.sleep(random.randint(4, 15))

    try:
        # grab the id from a search results page
        school_id = get_school_id(driver, d.name, d.city)
    except (NoSuchElementException, HTTPException) as e:
        logger.error(e)
        school_id = None

    new_url = d.url

    if d.url.strip() == 'NULL':
        new_url = None

    elif d.url[:4].lower() not in ['www.', 'http']:
        new_url = None

    elif d.url.startswith('www'):
        new_url = 'http://' + d.url

    s = School(name=d.name,
               sid=school_id,
               loc_state=d.state,
               loc_city=d.city,
               loc_zip=d.zipcode,
               url=new_url)

    session.add(s)
    session.commit()

    if school_id is not None:
        logger.info('Grabbing comments: ' + d.name)
        comments = get_school_comments(driver, school_id, MAX_COMMENTS)
        session.add_all(comments)
        session.commit()

    session.close()

    # force closing hanging process
    driver.service.process.send_signal(signal.SIGTERM)
    driver.quit()

    logger.info('Finished: %s, took %0.2f' % (d.name, time.time()-s_time))


if __name__ == '__main__':
    # randomize our list so it's not as obvious we're going alphabetically
    # through the known registered schools in the United States.
    random.shuffle(school_list)

    logger.info('Starting execution with %d workers' % WORKER_COUNT)

    # spread the work across a pool..
    with mp.Pool(processes=WORKER_COUNT) as pool:
        results = pool.map(get_school_id_worker, school_list)

    print('done')
