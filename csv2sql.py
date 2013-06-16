#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Creates and runs SQL query for website from the given CSV file.
"""

import argparse
import csv
import MySQLdb
import os
import sys

from HTMLParser import HTMLParser
from mysql_info import *


class TweetParser:
    def __init__(self, filename):
        try:
            self.db = MySQLdb.connect(MYSQL_HOST, MYSQL_USER, MYSQL_PASS,
                                      MYSQL_BASE, charset='utf8')
        except MySQLdb.OperationalError, e:
            print e.args[1]
            sys.exit(1)

        self.cursor = self.db.cursor()
        self.filename = filename
        self.parse_csv()

    def __del__(self):
        try:
            if self.db:
                self.db.close()
        except AttributeError:
            pass

    def insert_tweet(self, tweet):
        self.cursor.execute("SELECT id FROM `django_content_type` WHERE "
                            "`app_label` = 'tweets' AND `model` = 'tweet';")
        content_type = int(self.cursor.fetchone()[0])
        try:
            self.cursor.execute("INSERT INTO `tweets_tweet` (`text`, `url`) "
                                "VALUES ('%s', '%s');" %
                                (self.db.escape_string(tweet.text),
                                 tweet.status_url()))
            tweet_id = self.db.insert_id()
            self.cursor.execute("INSERT INTO `django_admin_log` "
                                "(`action_time`, `user_id`, `content_type_id`,"
                                "`object_id`,`object_repr`,`action_flag`, "
                                "`change_message`) VALUES(CURRENT_TIMESTAMP, "
                                "1, %d, %d, '%s', 1, '');" %
                                (content_type, tweet_id,
                                 self.db.escape_string(tweet.text)))
            self.db.commit()
        except MySQLdb.Error, e:
            self.db.rollback()

    def parse_csv(self):
        with open(self.filename) as f:
            tweets = csv.reader(f, quoting=csv.QUOTE_NONNUMERIC)
            for i in reversed(list(tweets)):
                t = Tweet(i[0], i[1], i[3])
                self.insert_tweet(t)


class Tweet:
    def __init__(self, id, screen_name, text=None):
        self.id = id
        self.screen_name = screen_name
        if text:
            self.text = text

    def status_url(self):
        return "https://twitter.com/%s/status/%s" % (self.screen_name, self.id)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.id


def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('file', help='CSV file containing tweets')

    args = parser.parse_args()
    if not os.path.exists(args.file):
        parser.error('File not found')

    TweetParser(args.file)


if __name__ == '__main__':
    main()
