from django.urls import path

from common.interfaces.views import health

urlpatterns = [
    path("health", health, name="health"),
]
