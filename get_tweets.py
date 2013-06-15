#!/usr/bin/python
# -*- coding: utf-8 -*-

import csv
import os
import re
from datetime import datetime

# This code uses a special version of tweepy 2.0 library
# Available here: https://github.com/inactivist/tweepy/tree/fix-v2-search
import tweepy

# This file contains application and user tokens for Twitter
import occupygezi_tokens

DATE_FORMAT = '%Y%m%d%H%M%S'
CSV_PREFIX = 'occupygezi'
TAG = '#OccupyGeziManifestosu'


def find_latest_csv():
    """Gets the latest date program ran and obtained data"""

    # Search filenames of data to find the newest one
    latest = None
    for f in os.listdir('.'):
        # Skip non-CSV files
        if os.path.splitext(f)[-1] != '.csv':
            continue

        # Skip CSV files not matching the pattern
        m = re.match(r'%s-([0-9]{14}).csv' % CSV_PREFIX, f)
        if not m:
            continue

        # Skip files with invalid timestamp
        mdate = m.groups()[0]
        try:
            date = datetime.strptime(mdate, DATE_FORMAT)
        except ValueError:
            continue

        # Tweet do not come from future
        if date > datetime.now():
            continue

        # After all these checks, if any left, find the newest
        if not latest or date > latest:
            latest = date

    return latest


def get_latest_id():
    """Gets the ID of the latest tweet from previous data"""

    # If there is not any data from previous runs,
    # search Twitter from beginning of the time
    date = find_latest_csv()
    if not date:
        return 0

    # Read CSV file to get latest tweet ID
    with open('%s-%s.csv' % (CSV_PREFIX, date.strftime(DATE_FORMAT))) as f:
        tweets = csv.reader(f, quoting=csv.QUOTE_NONNUMERIC)
        latest_id = 0
        for tweet in tweets:
            id = tweet[0]
            if id > latest_id:
                latest_id = id
        return latest_id


def get_status_url(screen_name, id):
    return "https://twitter.com/%s/status/%s" % (screen_name, id)


def main():
    # Consumer tokens for your application
    auth = tweepy.OAuthHandler(occupygezi_tokens.CONSUMER_KEY,
                               occupygezi_tokens.CONSUMER_SECRET)
    # Access tokens for user
    auth.set_access_token(occupygezi_tokens.ACCESS_TOKEN,
                          occupygezi_tokens.ACCESS_SECRET)

    # Initialize Twitter API with authorization information
    api = tweepy.API(auth)

    # Get latest tweet ID from previous runs
    latest_id = get_latest_id()

    # Write tweets into a brand new CSV file
    date = datetime.now()
    filename = '%s-%s.csv' % (CSV_PREFIX, date.strftime(DATE_FORMAT))
    with file(filename, 'w') as f:
        tweets = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)

        # Search Twitter
        items = tweepy.Cursor(api.search, q=TAG,
                              count=100, since_id=latest_id,
                              result_type='recent').items()

        for tweet in items:
            # Skip retweets
            if tweet.text.startswith('RT @'):
                continue

            id = tweet.id_str
            name = tweet.user.screen_name
            text = tweet.text.replace('\n', ' ').encode('utf8')
            # Remove hashtag from tweets
            text = re.sub(TAG, '', text, flags=re.IGNORECASE)
            # Replace multiple spaces with single spaces
            text = re.sub(r'\s{2,}', ' ', text).strip()
            tweets.writerow([id, name, get_status_url(name, id), text])

    # If there aren't any tweets, delete the CSV file
    if items.count == 0:
        os.unlink(filename)

# If script is not run directly, do nothing
if __name__ == '__main__':
    main()
