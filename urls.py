

from django.urls import path
from django_twitter_mining import views
from django.conf.urls import url

urlpatterns = [
    url(r'^trends/(?P<woe_id>[0-9]+)/$', views.trends),
    url(r'^search/(?P<q>[0-9a-zA-Z]+)/$', views.search),
    url(r'^stream/(?P<q>[0-9a-zA-Z]+)/$', views.streaming_results),
]
