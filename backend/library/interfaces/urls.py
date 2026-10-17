from django.urls import path

from library.interfaces import views

urlpatterns = [
    path("", views.books, name="library-books"),
    path("my-requests", views.my_requests, name="library-my-requests"),
    path("reports", views.create_report, name="library-report-create"),
    path("wishes", views.create_wish, name="library-wish-create"),
    path("<int:book_id>", views.book_detail, name="library-book-detail"),
]
