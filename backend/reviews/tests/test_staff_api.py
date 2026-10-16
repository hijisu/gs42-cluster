from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.domain.role import Role
from accounts.infrastructure.models import User
from common.infrastructure.event_bus import event_bus
from reviews.domain.events import ReviewRequested
from reviews.infrastructure.models import CourseParticipant, CourseRow, ReviewRow

pytestmark = pytest.mark.django_db
TODAY = timezone.localdate()


@pytest.fixture(autouse=True)
def _mock_login(settings):
    settings.MOCK_LOGIN_ENABLED = True


@pytest.fixture
def events():
    captured = []
    event_bus.subscribe(ReviewRequested, captured.append)
    yield captured
    event_bus._handlers[ReviewRequested].remove(captured.append)


def login(role):
    client = APIClient()
    client.post("/api/auth/mock-login", {"role": role}, format="json")
    return client


@pytest.fixture
def staff():
    return login("staff")


def body(**kw):
    return {
        "name": "서울대학교 파이썬 AI 교육",
        "start_date": (TODAY - timedelta(days=12)).isoformat(),
        "end_date": (TODAY - timedelta(days=3)).isoformat(),
        "location": "온라인",
        "status": "completed",
        "review_deadline": (TODAY + timedelta(days=7)).isoformat(),
        "intra_ids": ["alice", "bob", "student"],
        **kw,
    }


def create(staff, **kw):
    response = staff.post("/api/staff/courses", body(**kw), format="json")
    assert response.status_code == 201, response.content
    return response.json()


STAFF_URLS = [
    ("get", "/api/staff/courses"),
    ("post", "/api/staff/courses"),
    ("get", "/api/staff/courses/1"),
    ("patch", "/api/staff/courses/1"),
    ("post", "/api/staff/courses/1/participants"),
    ("post", "/api/staff/courses/1/review-request"),
]


@pytest.mark.parametrize(("method", "url"), STAFF_URLS)
def test_students_403_and_anonymous_401(method, url):
    assert getattr(login("student"), method)(url, {}, format="json").status_code == 403
    assert getattr(APIClient(), method)(url, {}, format="json").status_code == 401


def test_create_course_with_participants_201(staff):
    data = create(staff)
    assert data["name"] == "서울대학교 파이썬 AI 교육" and data["participant_count"] == 3
    assert [p["intra_id"] for p in data["participants"]] == ["alice", "bob", "student"]
    assert (data["reviewed_count"], data["pending_count"], data["review_rate"]) == (0, 3, 0.0)
    assert CourseParticipant.objects.filter(course_id=data["id"]).count() == 3


def test_create_accepts_csv_and_merges_with_list(staff):
    data = create(staff, intra_ids=["alice"], csv="intra_id\nBob, carol\n")
    assert [p["intra_id"] for p in data["participants"]] == ["alice", "bob", "carol"]


@pytest.mark.parametrize(
    "bad",
    [
        {"name": ""},
        {"end_date": (TODAY - timedelta(days=40)).isoformat()},
        {"review_deadline": (TODAY - timedelta(days=9)).isoformat()},
        {"intra_ids": ["alice", "bad id!"]},
        {"status": "weird"},
    ],
)
def test_create_validation_400_and_nothing_saved(staff, bad):
    assert staff.post("/api/staff/courses", body(**bad), format="json").status_code == 400
    assert CourseRow.objects.count() == 0


def test_invalid_intra_id_has_code(staff):
    response = staff.post("/api/staff/courses", body(intra_ids=["alice", "bad id!"]), format="json")
    assert response.json()["code"] == "invalid_intra_id"


def test_list_shows_participation_and_review_rate(staff):
    course = create(staff, intra_ids=["student", "alice", "bob", "carol"])
    student = login("student")
    student.post(
        "/api/reviews", {"course_id": course["id"], "rating": 5, "title": "좋았어요"}, format="json"
    )
    (row,) = staff.get("/api/staff/courses").json()
    assert (row["participant_count"], row["reviewed_count"], row["pending_count"]) == (4, 1, 3)
    assert row["review_rate"] == 0.25 and "participants" not in row


def test_detail_marks_who_reviewed_without_leaking_anonymous_text(staff):
    course = create(staff)
    login("student").post(
        "/api/reviews",
        {"course_id": course["id"], "rating": 4, "title": "익명", "anonymous": True},
        format="json",
    )
    detail = staff.get(f"/api/staff/courses/{course['id']}").json()
    reviewed = {p["intra_id"]: p["reviewed"] for p in detail["participants"]}
    assert reviewed == {"alice": False, "bob": False, "student": True}


def test_detail_unknown_404(staff):
    assert staff.get("/api/staff/courses/999").status_code == 404


def test_patch_status_opens_reviews_for_students(staff):
    course = create(staff, status="ongoing")
    student = login("student")
    payload = {"course_id": course["id"], "rating": 5, "title": "t"}
    assert student.post("/api/reviews", payload, format="json").json()["code"] == "review_closed"
    patched = staff.patch(
        f"/api/staff/courses/{course['id']}", {"status": "completed"}, format="json"
    )
    assert patched.status_code == 200 and patched.json()["status"] == "completed"
    assert student.post("/api/reviews", payload, format="json").status_code == 201


def test_patch_invalid_rolls_back(staff):
    course = create(staff)
    response = staff.patch(
        f"/api/staff/courses/{course['id']}",
        {"name": "새 이름", "end_date": (TODAY - timedelta(days=99)).isoformat()},
        format="json",
    )
    assert response.status_code == 400 and response.json()["code"] == "invalid_course"
    assert CourseRow.objects.get(pk=course["id"]).name == "서울대학교 파이썬 AI 교육"


def test_patch_can_clear_deadline(staff):
    course = create(staff)
    patched = staff.patch(
        f"/api/staff/courses/{course['id']}", {"review_deadline": None}, format="json"
    )
    assert patched.json()["review_deadline"] is None


def test_add_participants_json_and_csv(staff):
    course = create(staff, intra_ids=["alice"])
    url = f"/api/staff/courses/{course['id']}/participants"
    first = staff.post(url, {"intra_ids": ["Alice", "dave"]}, format="json").json()
    assert (first["added"], first["existing"]) == (["dave"], ["alice"])
    second = staff.post(url, {"csv": "intra_id\nerin\nfrank,dave"}, format="json").json()
    assert (second["added"], second["existing"]) == (["erin", "frank"], ["dave"])
    assert second["course"]["participant_count"] == 4


def test_add_participants_validation(staff):
    course = create(staff)
    url = f"/api/staff/courses/{course['id']}/participants"
    assert staff.post(url, {}, format="json").status_code == 400
    assert (
        staff.post(url, {"csv": "ok,not ok!"}, format="json").json()["code"] == "invalid_intra_id"
    )
    assert (
        staff.post("/api/staff/courses/999/participants", {"csv": "a1"}, format="json").status_code
        == 404
    )
    assert CourseParticipant.objects.filter(course_id=course["id"]).count() == 3


def test_participant_registered_before_signup_can_review_after_login(staff):
    course = create(staff, intra_ids=["student"])  # 로그인 전에 이미 등록됨
    assert not User.objects.filter(intra_id="student").exists()
    student = login("student")  # 이제서야 가입(로그인)
    assert student.get("/api/reviews/todo").json()[0]["id"] == course["id"]


def test_review_request_all_and_pending_with_events(staff, events):
    course = create(staff, intra_ids=["student", "alice", "bob"])
    login("student").post(
        "/api/reviews", {"course_id": course["id"], "rating": 5, "title": "t"}, format="json"
    )
    url = f"/api/staff/courses/{course['id']}/review-request"

    everyone = staff.post(
        url, {"target": "all", "message": "후기 부탁드려요"}, format="json"
    ).json()
    assert (
        everyone["recipients"] == ["alice", "bob", "student"] and everyone["recipient_count"] == 3
    )

    pending = staff.post(url, {"target": "pending"}, format="json").json()
    assert pending["recipients"] == ["alice", "bob"]

    assert [e.intra_ids for e in events] == [("alice", "bob", "student"), ("alice", "bob")]
    assert events[0].message == "후기 부탁드려요" and events[0].course_id == course["id"]


def test_review_request_validation_and_closed_course(staff, events):
    course = create(staff)
    url = f"/api/staff/courses/{course['id']}/review-request"
    assert staff.post(url, {"target": "nobody"}, format="json").status_code == 400
    assert staff.post(url, {}, format="json").status_code == 400
    ongoing = create(staff, name="진행 중", status="ongoing")
    closed = staff.post(
        f"/api/staff/courses/{ongoing['id']}/review-request", {"target": "all"}, format="json"
    )
    assert closed.status_code == 409 and closed.json()["code"] == "review_closed"
    assert (
        staff.post(
            "/api/staff/courses/999/review-request", {"target": "all"}, format="json"
        ).status_code
        == 404
    )
    assert events == []


def test_review_request_with_nobody_pending_is_empty_and_silent(staff, events):
    course = create(staff, intra_ids=["student"])
    login("student").post(
        "/api/reviews", {"course_id": course["id"], "rating": 5, "title": "t"}, format="json"
    )
    result = staff.post(
        f"/api/staff/courses/{course['id']}/review-request", {"target": "pending"}, format="json"
    ).json()
    assert result["recipient_count"] == 0 and events == []


def test_review_rows_by_non_participants_do_not_inflate_rate(staff):
    course = create(staff, intra_ids=["alice"])
    outsider = User.objects.create_user("zed", name="zed", role=Role.STUDENT.value)
    ReviewRow.objects.create(course_id=course["id"], author=outsider, rating=3, title="x")
    (row,) = staff.get("/api/staff/courses").json()
    assert row["reviewed_count"] == 0 and row["review_rate"] == 0.0
