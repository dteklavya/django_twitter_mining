# django_twitter_mining/tasks.py

from celery import shared_task
from .models import twitter_Search
from django_twitter_auth.models import oauth_twitter_login, app_twitter_login
from django_twitter_mining.models import twitter_Search

@shared_task
def get_search_results(user, q):
    twitter_api = oauth_twitter_login(None, user)
    return twitter_Search(twitter_api, q)


@shared_task
def start_app_search(q):
    twitter_api = app_twitter_login()
    return twitter_Search(twitter_api, q)
