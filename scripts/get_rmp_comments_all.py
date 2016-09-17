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
import threading as th
from queue import Queue

from logbook import Logger, StreamHandler
from sqlalchemy import func

from vivint.db.core import connect, session_factory
from vivint.db.models import SchoolComment
from vivint.grab.ratemyprof import get_driver, get_school_comments

logger = Logger(__name__)
StreamHandler(sys.stdout).push_application()

# process constants
WORKER_COUNT = 1
MAX_COMMENTS = 1000
RESCAN_MIN_COUNT = 90
CONN_STRING = 'sqlite:///./data/school-data.original.db'

# setup0 the database
engine = connect(CONN_STRING, echo=True, pool_recycle=3600)
get_session = session_factory(engine)

queue = Queue()


def do_work(driver, item):
    # starttt the timer weeeeehoooo!
    s_time = time.time()

    # unpack the db results
    school_id, o_comment_count = item

    logger.info('Starting: %d' % school_id)

    comments = get_school_comments(driver, school_id, MAX_COMMENTS)

    # allocate a database session
    session = get_session()

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

    # wrap it up, yo
    logger.info('Finished: %s, took %0.2f' % (school_id, time.time()-s_time))
    logger.info('%d ---> new, %d' % (o_comment_count, len(comments)))


def get_school_comments_worker():
    driver = get_driver()  # allocate a PhantomJS driver

    while True:
        item = queue.get()
        if item is None:
            # force closing hanging process
            driver.service.process.send_signal(signal.SIGTERM)
            driver.quit()
            break

        do_work(driver, item)
        queue.task_done()

    logger.info('Stopping thread')


if __name__ == '__main__':
    # randomize our list so it's not as obvious we're going alphabetically
    # through the known registered schools in the United States.
    logger.info('Starting execution with %d workers' % WORKER_COUNT)

    session = get_session()

    schools = session.query(SchoolComment.school_id, func.count(SchoolComment.id))\
        .group_by(SchoolComment.school_id)\
        .having(func.count(SchoolComment.school_id) >= RESCAN_MIN_COUNT)\
        .having(func.count(SchoolComment.school_id) <= 99)\
        .all()

    print(len(schools))

    random.shuffle(schools)
    threads = []

    for s in schools:
        queue.put_nowait(s)
    session.close()

    for i in range(WORKER_COUNT):
        t = th.Thread(target=get_school_comments_worker)
        t.start()
        threads.append(t)

    queue.join()

    for i in range(WORKER_COUNT):
        queue.put(None)
    for t in threads:
        t.join()

    print('done')
