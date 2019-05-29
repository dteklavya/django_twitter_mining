from django.shortcuts import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from django.views.decorators.http import require_http_methods

from django_twitter_auth.models import *

from .models import *

# Create your views here.


@login_required
def trends(request, woe_id=55959675):

    twitter_api = oauth_twitter_login(request.user)

    return JsonResponse(twitter_trends(twitter_api, woe_id), safe=False)


@login_required
@require_http_methods(["POST"])
def search(request):
    q = request.POST.get('q', '')

    if not q:
        return HttpResponseRedirect(request.build_absolute_uri('/'))

    twitter_api = oauth_twitter_login(request, request.user)

    return JsonResponse(twitter_Search(twitter_api, q), safe=False)


@login_required
def streaming_results(request, q):
    # Return the Streaming response to client.
    return StreamingHttpResponse(stream_results_generator(request.user, q))


@login_required
def search_popular(request, q):
    twitter_api = oauth_twitter_login(request.user)

    return JsonResponse(twitter_Search(twitter_api, q, popular=True), safe=False)
