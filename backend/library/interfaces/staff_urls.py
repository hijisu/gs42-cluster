from django.urls import path

from library.interfaces import staff_views as views

staff_urlpatterns = [
    path("books", views.create_book, name="staff-book-create"),
    path("books/<int:book_id>", views.book_detail, name="staff-book-detail"),
    path("book-reports", views.reports, name="staff-book-reports"),
    path(
        "book-reports/<int:report_id>/resolve",
        views.resolve_report,
        name="staff-book-report-resolve",
    ),
    path("book-wishes", views.wishes, name="staff-book-wishes"),
    path("book-wishes/<int:wish_id>", views.update_wish, name="staff-book-wish-update"),
]
