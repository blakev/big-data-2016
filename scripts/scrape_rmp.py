#! /usr/local/bin/python
# ~*~ encoding: utf-8 ~*~

import random
from urlparse import urlparse

from logbook import Logger
from selenium.webdriver import PhantomJS
from selenium.webdriver.common.by import By


class Config(object):
    search_url = r'https://www.ratemyprofessors.com/search.jsp?query={query}'
    campus_url = r'https://www.ratemyprofessors.com/campusRatings.jsp?sid={school_id}'
    # ~~
    driver = PhantomJS


class CSS(object):
    school_listing = (By.CSS_SELECTOR, 'li.listing.SCHOOL')


schools = [
    'Utah Valley University',
    'Brigham Young University',
    'Dixie State University'
]

random.shuffle(schools)


def get_school_id(school):
    """
        Args:
             school (str)

        Returns:
            int
    """
    logger = Logger('rmp.get_school_id.' + school)
    driver = PhantomJS()

    # iterate over each of the schools in our list
    normal_name = school.replace(' ', '+').lower()

    # search for our school
    driver.get(Config.search_url.format(query=normal_name))

    # get all the results that are school
    school_results = driver.find_elements(*CSS.school_listing)

    if not school_results:
        logger.error('Could not find a school result')
        return None

    row = school_results[0]
    href = row.find_element(By.TAG_NAME, 'a').get_attribute('href')

    if not href:
        logger.error('Could not find a link in the school result')
        return None

    school_id = urlparse(href).query.split('sid=')[-1]
    return int(school_id)

while True:
    print