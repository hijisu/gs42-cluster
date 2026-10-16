from django.urls import path

from accounts.interfaces import views

auth_urlpatterns = [
    path("login", views.login_redirect, name="auth-login"),
    path("callback", views.callback, name="auth-callback"),
    path("me", views.me, name="auth-me"),
    path("logout", views.logout_view, name="auth-logout"),
    path("mock-login", views.mock_login, name="auth-mock-login"),
]

staff_urlpatterns = [
    path("ping", views.staff_ping, name="staff-ping"),
]
