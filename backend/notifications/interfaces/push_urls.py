from django.urls import path

from notifications.interfaces import push_views

push_urlpatterns = [
    path("public-key", push_views.public_key, name="push-public-key"),
    path("subscriptions", push_views.subscriptions, name="push-subscriptions"),
]
