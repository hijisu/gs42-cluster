from django.urls import path

from reviews.interfaces import views

course_urlpatterns = [
    path("<int:course_id>/reviews", views.course_reviews, name="course-reviews"),
]
review_urlpatterns = [
    path("todo", views.todo, name="reviews-todo"),
]
