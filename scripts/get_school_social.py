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

import re
import sys
import random
import signal
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from logbook import Logger, StreamHandler

from vivint.db.core import connect, session_factory, create_tables
from vivint.db.models import School, SchoolSocial

StreamHandler(sys.stdout).push_application()
logger = Logger(__name__)


# process constants
MAX_WORKERS = 30
CONN_STRING = 'sqlite:///./data/school-data.original.db'
SOCIAL = {
    'facebook': None,
    'instagram': None,
    'pinterest': None,
    'plus.google': None,
    'twitter': None,
    'youtube': None,
    'mailto:': None
}

# setup the database
engine = connect(CONN_STRING, echo=True, pool_recycle=3600)
create_tables(engine)
get_session = session_factory(engine)


# def get_links(driver) -> dict:
#     links = driver.find_elements_by_tag_name('a')
#     ret_dict = {}
#
#     for link in map(lambda a: a.get_attribute('href'), links):
#         for site in SOCIAL.keys():
#             if site + '.com' in link:
#                 ret_dict.setdefault(site, link)
#
#         if len(ret_dict) == len(SOCIAL):
#             break
#
#     return ret_dict
#
#
# def find_social_links(row):
#     driver = get_driver()
#     session = get_session()
#
#     name, school_id, url = row
#     social_links = None
#
#     if driver is None:
#         logger.error('SKIPPING ' + name)
#         session.close()
#         return name, social_links
#
#     try:
#         driver.get(url)
#         social_links = get_links(driver)
#     except Exception:
#         logger.error('SKIPPING via ERROR ' + name)
#
#     if social_links:
#         s_copy = dict(SOCIAL)
#         s_copy.update(social_links)
#         s_copy['google_plus'] = s_copy.pop('plus.google', None)
#         s_obj = SchoolSocial(school_id=school_id, **s_copy)
#         session.add(s_obj)
#         session.commit()
#
#     # force closing hanging process
#     driver.service.process.send_signal(signal.SIGTERM)
#     driver.quit()
#     session.close()
#
#     return name, social_links

social_regex = re.compile(r'(facebook|instagram|pinterest|plus\.google|twitter|youtube|mailto\:)', re.I)


def find_social(href):
    return href and social_regex.search(href)


def load_url(row, timeout):
    name, school_id, url = row

    with urllib.request.urlopen(url, timeout=timeout) as conn:
        page = conn.read()
        bs = BeautifulSoup(page, 'lxml')

        links = bs.find_all(href=find_social)

        if links:
            # make a copy of the empty dictionary
            social = dict(SOCIAL)

            for a in links:
                href = a.attrs.get('href')
                for key in social.keys():
                    if key in href:
                        social[key] = href

            social['google_plus'] = social.pop('plus.google')
            social['email'] = social.pop('mailto:')

            session = get_session()
            s = SchoolSocial(**social)
            s.school_id = school_id
            session.add(s)
            session.commit()

        else:
            session = get_session()
            s = SchoolSocial(school_id=school_id)
            session.add(s)
            session.commit()
        return True


with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
    session = get_session()

    found = session.query(SchoolSocial.school_id)
    rows = session.query(School).\
        filter(School.id.notin_(found)).\
        filter(School.url.isnot(None))

    rows = [(r.name, r.id, r.url,) for r in rows]
    session.close()

    random.shuffle(rows)

    print(len(rows))

    future_to_url = {pool.submit(load_url, r, 10): r for r in rows}

    for future in as_completed(future_to_url):
        row = future_to_url[future]
        try:
            data = future.result()
        except Exception as e:
            name, school_id, url = row
            logger.error('%s, %s' % (url, e))
        else:
            pass
    #
    # for found in pool.imap_unordered(find_social_links, rows):
    #     print(found)
    #
