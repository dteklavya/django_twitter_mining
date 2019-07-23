from django.db import models

# Create your models here.

import pymongo
import json
import time
from bson import ObjectId
import datetime
import sys

from django_twitter_auth.models import *


def save_to_mongo(data, mongo_db, mongo_db_coll, **mongo_conn_kw):
    # Connects to the MongoDB server running on
    # localhost:27017 by default
    client = pymongo.MongoClient(**mongo_conn_kw)
    # Get a reference to a particular database
    db = client[mongo_db]
    # Reference a particular collection in the database
    coll = db[mongo_db_coll]
    # Perform a bulk insert and return the IDs
    # FIXME: Why should insert_many overwrite the 'data', it messes up the JSON encoder.
    num_inserted = coll.insert_many(data)
    return num_inserted


def load_from_mongo(mongo_db, mongo_db_coll, return_cursor=False,
                    criteria=None, projection=None, **mongo_conn_kw):
    # Optionally, use criteria and projection to limit the data that is
    # returned as documented in
    # http://docs.mongodb.org/manual/reference/method/db.collection.find/
    # Consider leveraging MongoDB's aggregations framework for more
    # sophisticated queries.
    client = pymongo.MongoClient(**mongo_conn_kw)
    db = client[mongo_db]
    coll = db[mongo_db_coll]
    if criteria is None:
        criteria = {}
    if projection is None:
        cursor = coll.find(criteria)
    else:
        cursor = coll.find(criteria, projection)
    # Returning a cursor is recommended for large amounts of data
    if return_cursor:
        return cursor
    else:
        return [ item for item in cursor ]


# Generator method. Return tweet text as they are posted/become available
def stream_results_generator(user, q):

    twitter_stream = oauth_twitter_streaming(user)

    stream = twitter_stream.statuses.filter(track=q)

    for tweet in stream:
        yield tweet['text']
        time.sleep(1)


def twitter_trends(twitter_api, woe_id):
    trends = twitter_api.trends.place(_id=woe_id)

    # Some basic filters for trending topics
    my_trends = []
    for trend in trends[0]['trends']:
        if trend['tweet_volume'] != None:
            my_trends.append({
                'name': trend['name'],
                'tweet_volume': trend['tweet_volume'],
                'url': trend['url']})

    return my_trends


def twitter_Search(twitter_api, q, max_results=200, popular=False, **kwargs):
    results = twitter_api.search.tweets(q=q, count=100, **kwargs)
    statuses = results['statuses']

    max_results = min(1000, max_results)
    for i in range(10):
        try:
            next_results = results['search_metadata']['next_results']
        except KeyError as e:
            break
        kw = dict([ kv.split('=')
                   for kv in next_results[1:].split('&') ])
        results = twitter_api.search.tweets(**kw)
        statuses += results['statuses']

        if len(statuses) > max_results:
            break

    if popular:
        statuses = get_popular_tweets(statuses)

    # Save the results in Mongo DB.
    # FIXME: Strangely, call to pymongo.insert rewrites the data sent to save.
    # That's the reason, using our custome JSON encoder.
    # This needs to be figured out.
    # if len(statuses):
    #     ni = save_to_mongo(statuses, 'search_results', q)

    # Figure out how and when to kick start the search? A POST from client or a config param?
    # TODO: Save search results/elements to DB or cache. HERE.
    # TODO: Write REST API calls to return search data. In main project reactDj.
    # TODO: Find a way to return status message on the quantum of tweets received and pending.
    # TODO: Use the twitter_analysis app to find, store and return tweet's sentiment.
    # TODO: Sentiment analysis must be done in Celery as async task with an API to feed the totals.

    return JSONEncoder().encode(statuses)


def twitter_time_Series_data(twitter_api, api_func, mongo_db_name, mongo_db_coll,
                             secs_per_interval=60, max_interval=15, **mongo_conn_kwargs):

    # Default settings of 15 intervals and 1 API call per interval ensure that
    # you will not exceed the Twitter rate limit.

    interval = 0

    while True:

        # A timestamp of the form '2018-12-17 15:39:39'
        now = str(datetime.datetime.now()).split(".")[0]

        ids = save_to_mongo(api_func(), mongo_db_name, mongo_db_coll, "-" + now)

        print("Write {0} trends".format(len(ids)), file=sys.stderr)
        print("Zzz...", file=sys.stderr)
        sys.stderr.flush()

        time.sleep(secs_per_interval) # seconds
        interval += 1
        if interval >= 15:
            break


def tweet_entities(statuses):

    screen_names, hashtags, urls, media, symbols = [], [], [], [], []

    if len(statuses) == 0:
        return screen_names, hashtags, urls, media, symbols

    screen_names = [ user_mention['screen_name']
                        for status in statuses
                            for user_mention in status['entities']['user_mention'] ]

    hashtags = [ hashtag['text']
                    for status in statuses
                        for hashtag in status['entities']['hashtags'] ]

    urls = [ url['expanded_url']
                for status in statuses
                    for url in status['entities']['urls'] ]

    symbols = [ symbol['txt']
                for status in statuses
                    for symbol in statuses['entities']['symbols'] ]

    # In some cases (search results), the media entity may not appear
    if status['entities'].has_key('media'):
        media = [ media['url']
                    for status in statuses
                        for media in status['entities']['media'] ]

    return screen_names, hashtags, urls, media, symbols


class JSONEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


def get_popular_tweets(statuses, retweet_threshold=3):

    st = [ status
                for status in statuses
                    if status['retweet_count'] > retweet_threshold ]

    for status in st:
        for k, v in enumerate(status):
            print(v)
#     with open('twitter_response/tweet_responses_json', mode='w', encoding='utf=8') as O:
#         print(json.dumps(status, indent=1), file=O)
    return st

