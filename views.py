from django.shortcuts import render

from django.shortcuts import redirect, render_to_response, HttpResponse
from django.shortcuts import HttpResponseRedirect
from django.contrib.auth import login as django_login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.http import StreamingHttpResponse

import json
import twitter
import time
from bson import ObjectId
import datetime
import sys

from django_twitter_auth.config import *
from django_twitter_auth.models import TwitterUser

from .models import *


def _oauth_twitter_login(request):
    tokens = TwitterUser.objects.filter(
        username=request.user).values_list('OAUTH_TOKEN', 'OAUTH_TOKEN_SECRET')
    oauth_token, oauth_token_secret = tokens[0][0], tokens[0][1]

    auth = twitter.oauth.OAuth(oauth_token, oauth_token_secret,
                                   CONSUMER_KEY, CONSUMER_SECRET)

    return twitter.Twitter(auth=auth)

# Create your views here.


@login_required
def trends(request, woe_id):

    twitter_api = _oauth_twitter_login(request)

    return JsonResponse(twitter_trends(twitter_api, woe_id), safe=False)


class JSONEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


@login_required
def search(request, q):
    twitter_api = _oauth_twitter_login(request)

    return HttpResponse(twitter_Search(twitter_api, q))


@login_required
def streaming_results(request, q):
    # Return the Streaming response to client.
    return StreamingHttpResponse(stream_results_generator(request, q))


# Generator method.
def stream_results_generator(request, q):

    tokens = TwitterUser.objects.filter(
        username=request.user).values_list('OAUTH_TOKEN', 'OAUTH_TOKEN_SECRET')
    oauth_token, oauth_token_secret = tokens[0][0], tokens[0][1]

    auth = twitter.oauth.OAuth(oauth_token, oauth_token_secret,
                                   CONSUMER_KEY, CONSUMER_SECRET)

    twitter_stream = twitter.TwitterStream(auth=auth)

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


def twitter_Search(twitter_api, q, max_results=200, **kwargs):
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

    # Save the results in Mongo DB.
    # FIXME: Strangely, call to pymongo.insert rewrites the data sent to save.
    # That's the reason, using our custome JSON encoder.
    # This needs to be figured out.
    if len(statuses):
        ni = save_to_mongo(statuses, 'search_results', q)
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
