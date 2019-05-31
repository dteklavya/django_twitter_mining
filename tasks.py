# django_twitter_mining/tasks.py

from celery import shared_task
from .models import twitter_Search
from django_twitter_auth.models import oauth_twitter_login
from django_twitter_mining.models import twitter_Search

@shared_task
def get_search_results(user, q):
    twitter_api = oauth_twitter_login(None, user)
    return twitter_Search(twitter_api, q)
