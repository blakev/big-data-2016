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

import os
import json

import tweepy
from logbook import Logger

logger = Logger(__name__)

# find where the credentials are stored
fpath, fname = os.path.split(__file__)
cred_folder = os.path.abspath(os.path.join(fpath, os.pardir, 'credentials'))
assert os.path.exists(cred_folder)

# load the credentials from disk; not tracked in source control
creds = json.load(open(os.path.join(cred_folder, 'credentials.json')))
creds = creds.get('twitter', {})

# connect to twitter
auth = tweepy.OAuthHandler(creds['consumer_key'], creds['consumer_secret'])
auth.set_access_token(creds['access_token'], creds['access_token_secret'])
api = tweepy.API(auth)


for u in api.search_users('Utah Valley University', 3):
    print(u)
