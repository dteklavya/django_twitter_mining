from django.shortcuts import render

from django.shortcuts import redirect, render_to_response, HttpResponse
from django.shortcuts import HttpResponseRedirect
from django.contrib.auth import login as django_login
from django.contrib.auth.decorators import login_required



import json
import twitter
from twitter.oauth_dance import parse_oauth_tokens
from twitter.oauth import read_token_file, write_token_file

import django_twitter_auth
from django_twitter_auth.config import *
from django_twitter_auth.models import TwitterUser

# Create your views here.

@login_required
def trends(request, woe_id):

    tokens = TwitterUser.objects.filter(
        username=request.user).values_list('OAUTH_TOKEN', 'OAUTH_TOKEN_SECRET')
    oauth_token, oauth_token_secret = tokens[0][0], tokens[0][1]

    auth = twitter.oauth.OAuth(oauth_token, oauth_token_secret,
                                   CONSUMER_KEY, CONSUMER_SECRET)

    twitter_api = twitter.Twitter(auth=auth)

    trends = twitter_api.trends.place(_id=woe_id)
#     print(json.dumps(trends, indent=1))

    # Some basic filters for trending topics
    my_trends = []
    for trend in trends[0]['trends']:
        if trend['tweet_volume'] != None:
            my_trends.append({
                'name': trend['name'],
                'tweet_volume': trend['tweet_volume'],
                'url': trend['url']})

    print(my_trends)
    return HttpResponse(json.dumps(my_trends, indent=1))


