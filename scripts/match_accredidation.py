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
import csv
import hashlib
from collections import namedtuple

from logbook import Logger
from fuzzywuzzy import fuzz, process

from vivint.db.core import connect, session_factory
from vivint.db.models import School as SchoolModel

logger = Logger(__name__)

csv_header = [
    'Institution_ID', 'Institution_Name', 'Institution_Address',
    'Institution_City', 'Institution_State', 'Institution_Zip',
    'Institution_Phone', 'Institution_OPEID', 'Institution_IPEDS_UnitID',
    'Institution_Web_Address', 'Campus_ID', 'Campus_Name', 'Campus_Address',
    'Campus_City', 'Campus_State', 'Campus_Zip', 'Campus_IPEDS_UnitID',
    'Accreditation_Type', 'Agency_Name', 'Agency_Status', 'Program_Name',
    'Accreditation_Status', 'Accreditation_Date_Type', 'Periods', 'Last Action'
]

skip_actions = [
    'Resigned', 'Terminated'
]

School = namedtuple('School', ' '.join(map(lambda s: s.replace(' ', '_').lower(), csv_header)))

# setup the database
engine = connect('sqlite:///./data/school-data.original.db', echo=True, pool_recycle=3600)
get_session = session_factory(engine)


# grab the raw list of schools from the CSV file
def get_schools(from_file=None):
    with open(from_file) as csv_in:
        reader = csv.reader(csv_in, delimiter=',', quotechar='"')
        for idx, row in enumerate(reader):
            if idx == 0:
                continue
            yield School(*row)


# get all the database rows where there is no URL set
session = get_session()
no_url_choices = list()
no_url_choices_dict = dict()
no_url_db = session.query(SchoolModel).filter(SchoolModel.url.is_(None)).all()
for school in no_url_db:
    s = '%s %s' % (school.name.rsplit('-', 1)[0], school.loc_state)
    no_url_choices.append(s)
    no_url_choices_dict[s] = school.id
session.close()

# get all the schools, uniquely, in the accreditation CSV that has
# a valid website
dedupe_dict = dict()
school_gen = get_schools(r'./data/accreditation_2015_03.csv')
# deduplicate campus locations, favor institution location
for school in filter(lambda x: x.last_action not in skip_actions, school_gen):
    s = school

    if not s.institution_web_address:
        continue

    prepare = {
        'name': s.institution_name,
        'addr': s.institution_address,
        'city': s.institution_city,
        'state': s.institution_state,
        'zip': s.institution_zip.strip('"').split('-')[0],
        'url': s.institution_web_address
    }

    s_hash = json.dumps(prepare, indent=0, sort_keys=True).encode('utf-8')
    s_hash = hashlib.md5(s_hash)

    prepare = dedupe_dict.setdefault(s_hash, prepare)

dedupe_choices = list()
dedupe_choices_dict = dict()
# line up the rows in our new dataset to see if we can find a match
for hash, school in dedupe_dict.items():
    s = '%s %s' % (school['name'], school['state'])
    dedupe_choices.append(s)
    dedupe_choices_dict[s] = hash

session = get_session()

# can we find a potential match??
for no_url_school in no_url_choices:
    x = process.extract(no_url_school, dedupe_choices, scorer=fuzz.token_set_ratio, limit=1)
    x = x[0]
    name, score = x

    if name[-2:] == no_url_school[-2:]:
        # check if they're in the same state
        print(no_url_school, name, score)

        if score >= 90:
            # if our match score is above 85, and it's in the same state
            # there's a very high chance it's the right school -- and we're going to
            # "take it" and put that as the new URL in the database.
            school_id = no_url_choices_dict.get(no_url_school)

            s = session.query(SchoolModel).filter(SchoolModel.id==school_id).one()
            p = dedupe_dict.get(dedupe_choices_dict.get(name))
            s.url = p.get('url')
            session.add(s)
            session.commit()
session.close()

