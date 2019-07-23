from django.shortcuts import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from django.views.decorators.http import require_http_methods

from django_twitter_auth.models import *

from celery import current_app
from .tasks import get_search_results, start_app_search

from .models import *

# Create your views here.


@login_required
def trends(request, woe_id=55959675):

    twitter_api = oauth_twitter_login(request.user)

    return JsonResponse(twitter_trends(twitter_api, woe_id), safe=False)

from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view

# @require_http_methods(["POST", "GET"])
# @login_required
@csrf_exempt
@api_view(['POST'])
def search(request):
    q = request.data.get('q', '')

    if not q:
        return HttpResponseRedirect(request.build_absolute_uri('/'))

    if not request.user.is_authenticated:
        twitter_api = oauth_twitter_login(request, request.user)

    # Call the Celery task to get search results from twitter and store it.
    # Where in Redis? RabitMQ? or SQL DB?

    task = get_search_results.delay(request.user.username, q)
    print(f"id={task.id}, state={task.state}, status={task.status}")

    # Return response to user that the task has been submitted.

    # Also, write a view to display task progress on browser.
    # return JsonResponse(twitter_Search(twitter_api, q), safe=False)
    return JsonResponse({'Response': 'Twitter Search has been kicked off!'})


@csrf_exempt
@api_view(['POST'])
def app_search(request):
    q = request.data.get('q', '')

    if not q:
        return JsonResponse({'Response': 'Bad search query'})

    task = start_app_search.delay(q)
    print(f"id={task.id}, state={task.state}, status={task.status}")

    return JsonResponse({'Response': 'Twitter Search has been kicked off with task ID: ' + task.id})


@login_required
def streaming_results(request, q):
    # Return the Streaming response to client.
    return StreamingHttpResponse(stream_results_generator(request.user, q))


@login_required
def search_popular(request, q):
    twitter_api = oauth_twitter_login(request.user)

    return JsonResponse(twitter_Search(twitter_api, q, popular=True), safe=False)
