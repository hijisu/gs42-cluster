from django.urls import path

from notifications.interfaces import views

urlpatterns = [
    path("read-all", views.read_all, name="notifications-read-all"),
    path("<int:notification_id>/read", views.read, name="notification-read"),
]
