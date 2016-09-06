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
import datetime
from typing import List, Tuple
from urllib.parse import urlparse
from collections import namedtuple

from logbook import Logger
from selenium.webdriver import PhantomJS
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

from vivint.db.models import School, SchoolComment

logger = Logger(__name__)
Teacher = namedtuple('Teacher', 'name tid')
WebDriver = PhantomJS   # alias for type completion

MAX_COMMENTS = 50

re_number = re.compile(r'\d+', re.I)
re_scores = re.compile(r'\>([\d\w ]+)\</', re.M + re.I)
re_state = re.compile(r' ([A-Z]{2})')


class Config(object):
    search_url = r'https://www.ratemyprofessors.com/search.jsp?queryBy=schoolName&queryoption=HEADER&query={query}&facetSearch=true'
    campus_url = r'https://www.ratemyprofessors.com/campusRatings.jsp?sid={school_id}'


class CSS(object):
    school_listing = (By.CSS_SELECTOR, 'li.listing.SCHOOL')
    school_header = (By.CSS_SELECTOR, 'div.result-title')
    school_name = (By.CSS_SELECTOR, 'div.result-name')
    school_overall_q = (By.CSS_SELECTOR, 'div.school-breakdown span.score')
    score_details = (By.CSS_SELECTOR, 'div.quality-breakdown div.rating')
    ratings_count = (By.CSS_SELECTOR, 'div.rating-count')


def get_driver():
    try:
        driver = PhantomJS()
        driver.implicitly_wait(3.0)
    except WebDriverException as e:
        logger.error(e)
        return None
    return driver


def get_school_id(driver, school: str, school_city: str=None) -> int:
    """ Grabs the RateMyProfessor school ID from a search results page. """

    # some schools have their city listed in the name...for some reason
    # this reduces the chances of finding that school on RMP. So, we remove
    # it if it's there...more or less.
    if school_city and isinstance(school_city, str):
        if school.lower().strip().endswith('-' + school_city.lower().strip()):
            school = school.rsplit('-', 1)[0]

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


# def get_school_details(driver, school_id: int) -> Tuple(int, dict):
#     """ Grabs the RateMyProfessor school details from ``campusRatings.jsp``"""
#
#     # load the overview page
#     driver.get(Config.campus_url.format(school_id=school_id))
#
#     # find the school attributes in the top-portion of the listing page
#     name = driver.find_element(*CSS.school_name).text
#     result_title = driver.find_element(*CSS.school_header)
#     location = result_title.find_element(By.TAG_NAME, 'span').text
#     website_url = result_title.find_element(By.TAG_NAME, 'a').get_attribute('href')
#
#     # get score values
#     overall = driver.find_element(*CSS.school_overall_q).text
#     overall = float(overall)
#
#     scores = {
#         'overall': overall
#     }
#
#     # get all the individual score boxes
#     score_boxes = driver.find_elements(*CSS.score_details)
#
#     for box in score_boxes:
#         score = box.find_element_by_css_selector('span.score').text
#         label = box.find_element_by_css_selector('span.label').text
#         scores.setdefault(label.lower(), float(score))
#
#     # parse location
#     state_code = re_state.search(location)
#
#     if state_code is None:
#         city, state = location, None
#     else:
#         state = state_code.group(0).strip()
#         city = location.split(state)[0].strip(' ,')
#
#     return School(sid=school_id,
#                   name=name,
#                   url=website_url,
#                   loc_city=city,
#                   loc_state=state,
#                   scores=scores)


def get_school_comments(driver,
                        school_id: int,
                        max_comments: int=MAX_COMMENTS) -> List[SchoolComment]:
    """ Grabs up to ``max_comments`` reviews from RateMyProfessor school details page. """

    # if one isn't supplied, we need to create a new one
    driver = driver or get_driver()

    # determine if we need to change pages or not
    url = Config.campus_url.format(school_id=school_id)
    if driver.current_url != url:
        driver.get(url)

    # determine if the school has any active ratings we can scrape
    ratings = driver.find_element(*CSS.ratings_count)
    rating_number = re_number.findall(ratings.text)
    if not rating_number:
        logger.error('Cannot find the ratings count for %d' % school_id)
        return list()
    else:
        rating_number = int(rating_number[0])

    # save the number of comments available per school
    comments = list()

    def get_shown_comments():
        els = driver.find_elements_by_css_selector('table.school-ratings tbody tr')
        return list(filter(lambda e: e.get_attribute('id') not in ['', None], els))

    if rating_number > 0:
        shown_comments = get_shown_comments()
        has_loadmore = True

        while has_loadmore and len(shown_comments) < max_comments:
            try:
                loadmore = driver.find_element(By.CSS_SELECTOR, 'a#loadMore[data-school-id="%d"]' % school_id)
                if loadmore:
                    has_loadmore = True
                    loadmore.click()
            except Exception as e:
                has_loadmore = False
            finally:
                shown_comments = get_shown_comments()

        for comment in shown_comments[1:max_comments+1]:
            # make sure the comment is visible, hopefully lazy loading its content
            driver.execute_script('arguments[0].scrollIntoView(true);', comment)

            # get scores / details
            scores = comment.find_element(By.CSS_SELECTOR, 'td.scores')
            score_section = scores.find_element(By.CSS_SELECTOR, 'div.rate-list')
            date_reviewed = scores.find_element(By.CSS_SELECTOR, 'div.date').text
            review_text = comment.find_element(By.CSS_SELECTOR, 'td.comments p').text

            # parse the date string on the page into an obj for SQL
            month, day, year = map(int, date_reviewed.split('/'))
            date_reviewed_obj = datetime.date(year, month, day)

            # for some reason we can't get the text from these web elements
            # through selenium. So, instead we're going to parse the html with
            # regex.
            inner_html = score_section.get_attribute('innerHTML')
            flatlist = re_scores.findall(inner_html)

            score_details = {}

            # group every other one together
            for score, label in zip(flatlist[::2], flatlist[1::2]):
                label = label.replace(' ', '_')
                score_details.setdefault(label.lower(), int(score))

            c = SchoolComment(school_id=school_id,
                              date_reviewed=date_reviewed_obj,
                              text=review_text,
                              **score_details)
            comments.append(c)
            logger.debug(len(comments))

    return comments


def get_school_teachers(school_id:int) -> List[Teacher]:
    pass


def get_teacher_details(teacher_id:int) -> dict:
    pass


def get_teacher_comments(teacher_id:int) -> List[dict]:
    pass

