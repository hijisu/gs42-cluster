from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.domain.role import Role
from accounts.infrastructure.models import User
from reviews.infrastructure.models import CourseParticipant, CourseRow, ReviewRow

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _mock_login(settings):
    settings.MOCK_LOGIN_ENABLED = True


def login(role="student"):
    client = APIClient()
    client.post("/api/auth/mock-login", {"role": role}, format="json")
    return client


def make_course(name="과정", status="completed", participants=("student",), deadline=14):
    today = timezone.localdate()
    # 진행 단계는 날짜로 계산된다(저장하지 않음)
    start, end = {"completed": (-20, -10), "ongoing": (-3, 5), "upcoming": (5, 12)}[status]
    course = CourseRow.objects.create(
        name=name,
        start_date=today + timedelta(days=start),
        end_date=today + timedelta(days=end),
        location="유니버스룸",
        review_deadline=today + timedelta(days=deadline) if deadline is not None else None,
    )
    for login_id in participants:
        CourseParticipant.objects.create(course=course, intra_id=login_id)
    return course


def payload(course, **kw):
    return {"course_id": course.pk, "rating": 5, "good": "좋았음", **kw}


def test_endpoints_require_login():
    for method, url in [
        ("get", "/api/courses"),
        ("get", "/api/courses/1/reviews"),
        ("get", "/api/reviews/todo"),
        ("post", "/api/reviews"),
    ]:
        assert getattr(APIClient(), method)(url).status_code == 401


def test_participant_posts_review_201():
    course = make_course()
    response = login().post(
        "/api/reviews", payload(course, tags=["#실습 위주", "입문"]), format="json"
    )
    assert response.status_code == 201
    data = response.json()
    assert data["rating"] == 5 and data["tags"] == ["실습 위주", "입문"] and data["mine"] is True
    assert data["author"] == {"intra_id": "student"}


def test_non_participant_gets_403():
    course = make_course(participants=("someone_else",))
    response = login().post("/api/reviews", payload(course), format="json")
    assert response.status_code == 403 and response.json()["code"] == "not_participant"
    assert ReviewRow.objects.count() == 0


def test_staff_who_is_not_participant_also_403():
    course = make_course()
    assert login("staff").post("/api/reviews", payload(course), format="json").status_code == 403


def test_participant_matching_is_case_insensitive():
    course = make_course(participants=("STUDENT",))
    assert login().post("/api/reviews", payload(course), format="json").status_code == 201


@pytest.mark.parametrize(
    ("kwargs", "status", "code"),
    [
        ({"status": "ongoing"}, 409, "review_closed"),
        ({"status": "upcoming"}, 409, "review_closed"),
        ({"deadline": -1}, 409, "review_closed"),
    ],
)
def test_closed_courses_409(kwargs, status, code):
    response = login().post("/api/reviews", payload(make_course(**kwargs)), format="json")
    assert response.status_code == status and response.json()["code"] == code


def test_duplicate_review_409():
    course = make_course()
    client = login()
    client.post("/api/reviews", payload(course), format="json")
    again = client.post("/api/reviews", payload(course), format="json")
    assert again.status_code == 409 and again.json()["code"] == "already_reviewed"
    assert ReviewRow.objects.count() == 1


def test_unknown_course_404():
    assert (
        login().post("/api/reviews", {"course_id": 999, "rating": 3}, format="json").status_code
        == 404
    )


@pytest.mark.parametrize(
    "bad", [{"rating": 0}, {"rating": 6}, {"tags": [f"t{i}" for i in range(6)]}]
)
def test_validation_400(bad):
    course = make_course()
    response = login().post("/api/reviews", {**payload(course), **bad}, format="json")
    assert response.status_code == 400


def test_db_constraints_back_up_the_rules():
    course = make_course()
    student = User.objects.create_user("db_user", name="x", role=Role.STUDENT.value)
    ReviewRow.objects.create(course=course, author=student, rating=3)
    from django.db import IntegrityError, transaction

    with pytest.raises(IntegrityError), transaction.atomic():
        ReviewRow.objects.create(course=course, author=student, rating=4)
    other = User.objects.create_user("db_user2", name="y", role=Role.STUDENT.value)
    with pytest.raises(IntegrityError), transaction.atomic():
        ReviewRow.objects.create(course=course, author=other, rating=9)


def test_anonymous_review_never_exposes_author_anywhere():
    course = make_course(participants=("student", "peer"))
    login().post("/api/reviews", payload(course, anonymous=True), format="json")
    for viewer in ("student", "staff"):
        response = login(viewer).get(f"/api/courses/{course.pk}/reviews")
        (review,) = response.json()
        assert review["anonymous"] is True and review["author"] is None
        assert "student" not in response.content.decode()  # 어디에도 intra_id가 없다
    # 작성자 본인은 mine 으로만 구분된다
    assert login("student").get(f"/api/courses/{course.pk}/reviews").json()[0]["mine"] is True
    assert login("staff").get(f"/api/courses/{course.pk}/reviews").json()[0]["mine"] is False


def test_non_anonymous_review_shows_author_intra_id():
    course = make_course()
    login().post("/api/reviews", payload(course, anonymous=False), format="json")
    (review,) = login("staff").get(f"/api/courses/{course.pk}/reviews").json()
    assert review["author"] == {"intra_id": "student"}


def test_reviews_of_unknown_course_404_and_newest_first():
    client = login()
    assert client.get("/api/courses/999/reviews").status_code == 404
    course = make_course(participants=("student", "peer"))
    peer = User.objects.create_user("peer", name="peer", role=Role.STUDENT.value)
    ReviewRow.objects.create(course=course, author=peer, rating=3, good="먼저")
    client.post("/api/reviews", payload(course, good="나중"), format="json")
    assert [r["good"] for r in client.get(f"/api/courses/{course.pk}/reviews").json()] == [
        "나중",
        "먼저",
    ]


def test_course_list_has_average_count_and_my_flags():
    done = make_course("끝난 과정")
    ongoing = make_course("진행 과정", status="ongoing")
    other = make_course("남의 과정", participants=("someone",))
    peer = User.objects.create_user("peer", name="peer", role=Role.STUDENT.value)
    ReviewRow.objects.create(course=done, author=peer, rating=3)
    client = login()
    client.post("/api/reviews", payload(done, rating=4), format="json")
    by_name = {c["name"]: c for c in client.get("/api/courses").json()}
    assert (
        by_name["끝난 과정"]["average_rating"] == 3.5 and by_name["끝난 과정"]["review_count"] == 2
    )
    assert (
        by_name["끝난 과정"]["participating"],
        by_name["끝난 과정"]["reviewed"],
        by_name["끝난 과정"]["can_review"],
    ) == (True, True, False)
    assert (
        by_name["진행 과정"]["can_review"] is False
        and by_name["진행 과정"]["participating"] is True
    )
    assert by_name["남의 과정"]["participating"] is False
    assert (
        by_name["남의 과정"]["average_rating"] is None and by_name["남의 과정"]["review_count"] == 0
    )
    assert {
        "id",
        "status",
        "start_date",
        "end_date",
        "review_deadline",
        "location",
        "intro",
    } <= set(by_name["끝난 과정"])
    assert ongoing.pk and other.pk


def test_todo_lists_only_pending_reviewable_courses_with_deadline():
    pending = make_course("작성 대기", deadline=5)
    done = make_course("작성 완료")
    make_course("마감", deadline=-2)
    make_course("진행 중", status="ongoing")
    make_course("남의 과정", participants=("x",))
    client = login()
    client.post("/api/reviews", payload(done), format="json")
    todo = client.get("/api/reviews/todo").json()
    assert [c["name"] for c in todo] == ["작성 대기"]
    assert todo[0]["review_deadline"] == (timezone.localdate() + timedelta(days=5)).isoformat()
    assert pending.pk == todo[0]["id"]


def test_review_has_no_title_and_course_list_has_board_fields():
    course = make_course("게시판 과정", participants=("student",))
    client = login()
    # 예전 클라이언트가 title을 보내도 무시된다(필수 아님, 응답에 없음)
    created = client.post("/api/reviews", {**payload(course), "title": "무시됨"}, format="json")
    assert created.status_code == 201 and "title" not in created.json()
    review = client.get(f"/api/courses/{course.pk}/reviews").json()[0]
    assert "title" not in review and review["good"] == "좋았음"

    item = next(c for c in client.get("/api/courses").json() if c["id"] == course.pk)
    assert {"name", "start_date", "end_date", "location", "review_count"} <= set(item)
    assert item["location"] == "유니버스룸" and item["review_count"] == 1


def _write_review(client, course, **over):
    body = {"course_id": course.pk, "rating": 3, "good": "원문", "tags": ["a"], "anonymous": False}
    return client.post("/api/reviews", {**body, **over}, format="json")


def test_author_edits_own_review_and_payload_reflects_it():
    course = make_course()
    client = login()
    review_id = _write_review(client, course).json()["id"]
    res = client.patch(
        f"/api/reviews/{review_id}",
        {"rating": 5, "good": "수정", "tags": ["#입문"], "anonymous": True},
        format="json",
    )
    assert res.status_code == 200
    body = res.json()
    assert (
        body["rating"] == 5
        and body["good"] == "수정"
        and body["tags"] == ["입문"]
        and body["mine"] is True
    )
    assert body["author"] is None  # 익명으로 바꿨다
    row = ReviewRow.objects.get(pk=review_id)
    assert (row.rating, row.good, row.anonymous) == (5, "수정", True)
    # 일부 항목만 보내면 나머지는 그대로
    client.patch(f"/api/reviews/{review_id}", {"bad": "아쉬움"}, format="json")
    row.refresh_from_db()
    assert (row.rating, row.good, row.bad) == (5, "수정", "아쉬움")
    stats = client.get("/api/courses").json()[0]
    assert stats["average_rating"] == 5.0 and stats["review_count"] == 1


def test_review_edit_is_author_only_and_has_no_delete():
    course = make_course(participants=("student", "other"))
    author = login()
    review_id = _write_review(author, course).json()["id"]
    other = APIClient()
    other.post(
        "/api/auth/mock-login", {"role": "student"}, format="json"
    )  # 같은 계정(student)이면 본인이므로 직접 사용자 생성
    stranger = User.objects.create(intra_id="other", role=Role.STUDENT.value)
    other.force_authenticate(stranger)
    res = other.patch(f"/api/reviews/{review_id}", {"rating": 1}, format="json")
    assert res.status_code == 403 and res.json()["code"] == "not_review_author"
    assert ReviewRow.objects.get(pk=review_id).rating == 3
    assert author.delete(f"/api/reviews/{review_id}").status_code == 405
    assert author.patch("/api/reviews/999999", {"rating": 1}, format="json").status_code == 404
    assert APIClient().patch(
        f"/api/reviews/{review_id}", {"rating": 1}, format="json"
    ).status_code in (401, 403)


def test_review_edit_validation_and_closed_period():
    course = make_course()
    client = login()
    review_id = _write_review(client, course).json()["id"]
    bad = client.patch(f"/api/reviews/{review_id}", {"rating": 9}, format="json")
    assert bad.status_code == 400
    too_many = client.patch(
        f"/api/reviews/{review_id}", {"tags": [f"t{i}" for i in range(6)]}, format="json"
    )
    assert too_many.status_code == 400 and too_many.json()["code"] == "invalid_review"
    # 마감일이 지나면 수정할 수 없다
    CourseRow.objects.filter(pk=course.pk).update(
        review_deadline=timezone.localdate() - timedelta(days=1)
    )
    closed = client.patch(f"/api/reviews/{review_id}", {"rating": 4}, format="json")
    assert closed.status_code == 409 and closed.json()["code"] == "review_closed"
    assert ReviewRow.objects.get(pk=review_id).rating == 3
