

from django.urls import path
from django_twitter_mining import views
from django.conf.urls import url

urlpatterns = [
    url(r'^trends/(?P<woe_id>[0-9]+)/$', views.trends),
    url(r'^search/$', views.app_search),
    url(r'^stream/(?P<q>[0-9a-zA-Z ]+)/$', views.streaming_results),
    url(r'^search_popular/(?P<q>[0-9a-zA-Z ]+)/$', views.search_popular),
]
