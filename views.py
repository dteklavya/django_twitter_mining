from django.shortcuts import render

from django.shortcuts import redirect, render_to_response, HttpResponse
from django.shortcuts import HttpResponseRedirect
from django.contrib.auth import login as django_login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse



import json
import twitter

from django_twitter_auth.config import *
from django_twitter_auth.models import TwitterUser


def _get_twitter_api(request):
    tokens = TwitterUser.objects.filter(
        username=request.user).values_list('OAUTH_TOKEN', 'OAUTH_TOKEN_SECRET')
    oauth_token, oauth_token_secret = tokens[0][0], tokens[0][1]

    auth = twitter.oauth.OAuth(oauth_token, oauth_token_secret,
                                   CONSUMER_KEY, CONSUMER_SECRET)

    return twitter.Twitter(auth=auth)


# Create your views here.

@login_required
def trends(request, woe_id):

    twitter_api = _get_twitter_api(request)

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

    print(json.dumps(my_trends, indent=1))
#     return HttpResponse(json.dumps(my_trends), content_type="application/json")
    return JsonResponse(my_trends, safe=False)


@login_required
def search(request, q, max_results=200, **kwargs):
    twitter_api = _get_twitter_api(request)

    results = twitter_api.search.tweets(q=q, count=100, **kwargs)
    statuses = results['statuses']

    return JsonResponse(statuses, safe=False)

