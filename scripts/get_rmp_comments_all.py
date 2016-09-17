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
#     big-data-2016, 2016 131561
# <<

import sys
import random
import signal
import time
import multiprocessing as mp

from logbook import Logger, StreamHandler
from sqlalchemy import func

from vivint.db.core import connect, session_factory
from vivint.db.models import SchoolComment
from vivint.grab.ratemyprof import get_driver, get_school_comments

logger = Logger(__name__)
StreamHandler(sys.stdout).push_application()

# process constants
WORKER_COUNT = 10
MAX_COMMENTS = 1000
RESCAN_MIN_COUNT = 90
CONN_STRING = 'sqlite:///./data/school-data.original.db'

# setup0 the database
engine = connect(CONN_STRING, echo=True, pool_recycle=3600)
get_session = session_factory(engine)


def get_school_comments_worker(s):
    s_time = time.time()

    # unpack the tuple
    school_id, o_comment_count = s

    driver = get_driver()    # allocate a PhantomJS driver

    if driver is None:
        logger.error('Driver error: %d' % school_id)
        return

    session = get_session()  # allocate a database session

    logger.info('Starting: %d' % school_id)

    time.sleep(random.randint(3, 10))

    comments = get_school_comments(driver, school_id, MAX_COMMENTS)

    if len(comments) > o_comment_count:
        logger.info('New comments found: %d' % school_id)
        # delete the original comments
        session.query(SchoolComment).filter(SchoolComment.school_id == school_id).delete()
        session.commit()
        # add all the new comments
        session.add_all(comments)
        session.commit()
    else:
        logger.info('Same comment count')

    # close the db connection
    session.close()

    # force closing hanging process
    driver.service.process.send_signal(signal.SIGTERM)
    driver.quit()

    # wrap it up, yo
    logger.info('Finished: %s, took %0.2f' % (school_id, time.time()-s_time))
    logger.info('%d ---> new, %d' % (o_comment_count, len(comments)))

if __name__ == '__main__':
    # randomize our list so it's not as obvious we're going alphabetically
    # through the known registered schools in the United States.
    logger.info('Starting execution with %d workers' % WORKER_COUNT)

    session = get_session()

    schools = session.query(SchoolComment.school_id, func.count(SchoolComment.id))\
        .group_by(SchoolComment.school_id)\
        .having(func.count(SchoolComment.school_id) >= RESCAN_MIN_COUNT)\
        .all()

    # spread the work across a pool..
    with mp.Pool(processes=WORKER_COUNT) as pool:
        results = pool.map(get_school_comments_worker, schools)

    session.close()

    print('done')
