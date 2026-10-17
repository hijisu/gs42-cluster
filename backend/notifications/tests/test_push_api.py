import logging
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from rest_framework.test import APIClient

from accounts.infrastructure.models import User
from common.infrastructure.dispatcher import InProcessEventDispatcher
from meetings.domain.events import MeetingConfirmed
from notifications.application.handlers import NotificationHandlers, register_handlers
from notifications.application.push import SubscriptionGone, WebPushNotifier
from notifications.application.service import NotificationService
from notifications.infrastructure.models import NotificationRow
from notifications.infrastructure.push import DjangoPushSubscriptionRepository
from notifications.infrastructure.push_models import PushSubscriptionRow
from notifications.infrastructure.repositories import DjangoUserDirectory, InAppNotifier
from notifications.infrastructure.vapid import generate_keys
from notifications.interfaces import wiring
from notifications.interfaces.push_config import load_push_config

pytestmark = pytest.mark.django_db
KST = ZoneInfo("Asia/Seoul")
FCM = "https://fcm.googleapis.com/fcm/send/"
KEY_A, KEY_B = "BEl62iUYgUivxIkv69yViEuiBIa-Ib9_", "tBHItJI5svbpez7KI4CCXg"


@pytest.fixture(autouse=True)
def _mock_login(settings):
    settings.MOCK_LOGIN_ENABLED = True


@pytest.fixture
def vapid(settings):
    public, private = generate_keys()
    settings.VAPID_PUBLIC_KEY = public
    settings.VAPID_PRIVATE_KEY = private
    return public, private


def login(role="student"):
    client = APIClient()
    client.post("/api/auth/mock-login", {"role": role}, format="json")
    return client


def body(n=1, **kw):
    return {
        "endpoint": f"{FCM}{n}",
        "expirationTime": None,
        "keys": {"p256dh": KEY_A, "auth": KEY_B},
        **kw,
    }


# ── 설정 ──
def test_push_is_off_without_a_private_key(settings):
    settings.VAPID_PRIVATE_KEY = ""
    assert load_push_config() is None
    assert [c.name for c in wiring.channels()] == ["in_app"]


def test_push_channel_is_added_when_configured(vapid):
    assert [c.name for c in wiring.channels()] == ["in_app", "web_push"]


def test_public_key_is_derived_from_the_private_key_even_if_env_public_key_is_wrong(
    settings, vapid, caplog
):
    other_public, _ = generate_keys()
    settings.VAPID_PUBLIC_KEY = other_public
    with caplog.at_level(logging.WARNING):
        config = load_push_config()
    assert config.public_key == vapid[0] and "짝이 아닙니다" in caplog.text


def test_broken_private_key_disables_push_instead_of_crashing(settings, caplog):
    settings.VAPID_PRIVATE_KEY = "this-is-not-a-key"
    with caplog.at_level(logging.ERROR):
        assert load_push_config() is None
        assert [c.name for c in wiring.channels()] == ["in_app"]
    assert "형식이 올바르지 않아" in caplog.text


# ── API ──
def test_endpoints_require_login():
    for method, url in [
        ("get", "/api/push/public-key"),
        ("post", "/api/push/subscriptions"),
        ("delete", "/api/push/subscriptions"),
    ]:
        assert getattr(APIClient(), method)(url).status_code == 401


def test_public_key_endpoint(vapid):
    response = login().get("/api/push/public-key")
    assert response.status_code == 200 and response.json() == {"public_key": vapid[0]}


def test_public_key_503_when_not_configured(settings):
    settings.VAPID_PRIVATE_KEY = ""
    response = login().get("/api/push/public-key")
    assert response.status_code == 503 and response.json()["code"] == "push_not_configured"


def test_subscribe_stores_the_browser_subscription_json(vapid):
    response = login().post("/api/push/subscriptions", body(), format="json")
    assert response.status_code == 201 and "id" in response.json()
    row = PushSubscriptionRow.objects.get()
    assert (row.endpoint, row.p256dh, row.auth, row.user.intra_id) == (
        f"{FCM}1",
        KEY_A,
        KEY_B,
        "student",
    )


def test_subscribe_without_configuration_is_503_and_stores_nothing(settings):
    settings.VAPID_PRIVATE_KEY = ""
    assert login().post("/api/push/subscriptions", body(), format="json").status_code == 503
    assert PushSubscriptionRow.objects.count() == 0


def test_subscribing_twice_updates_instead_of_duplicating(vapid):
    client = login()
    client.post("/api/push/subscriptions", body(), format="json")
    client.post("/api/push/subscriptions", body(), format="json")
    assert PushSubscriptionRow.objects.count() == 1


def test_one_user_can_have_several_devices(vapid):
    client = login()
    client.post("/api/push/subscriptions", body(1), format="json")
    client.post("/api/push/subscriptions", body(2), format="json")
    assert PushSubscriptionRow.objects.count() == 2


def test_same_browser_logging_in_as_another_user_takes_over_the_subscription(vapid):
    login("student").post("/api/push/subscriptions", body(), format="json")
    login("staff").post("/api/push/subscriptions", body(), format="json")
    row = PushSubscriptionRow.objects.get()
    assert row.user.intra_id == "staff"  # 이전 사용자의 알림이 이 브라우저로 가지 않는다


@pytest.mark.parametrize(
    "bad",
    [
        {"endpoint": "https://internal.example.com/x"},
        {"endpoint": "http://fcm.googleapis.com/fcm/send/1"},
        {"endpoint": "https://169.254.169.254/latest/meta-data/"},
        {"endpoint": "https://fcm.googleapis.com:abc/push"},  # bug #85: 500 이 아니라 400
        {"endpoint": "https://fcm.googleapis.com:65536/push"},
        {"endpoint": "https://[broken/push"},
        {"keys": {"p256dh": "not base64!", "auth": KEY_B}},
        {"keys": {"p256dh": KEY_A}},
        {"keys": None},
    ],
)
def test_invalid_subscriptions_are_rejected_with_400(vapid, bad):
    response = login().post("/api/push/subscriptions", body(**bad), format="json")
    assert response.status_code == 400
    assert PushSubscriptionRow.objects.count() == 0


def test_invalid_endpoint_has_a_stable_error_code(vapid):
    response = login().post(
        "/api/push/subscriptions", body(endpoint="https://evil.com/x"), format="json"
    )
    assert response.json()["code"] == "invalid_subscription"


def test_unsubscribe_removes_only_own_subscription_and_is_idempotent(vapid):
    mine, theirs = login("student"), login("staff")
    mine.post("/api/push/subscriptions", body(1), format="json")
    theirs.post("/api/push/subscriptions", body(2), format="json")
    assert (
        mine.delete("/api/push/subscriptions", {"endpoint": f"{FCM}2"}, format="json").status_code
        == 204
    )
    assert PushSubscriptionRow.objects.count() == 2  # 남의 구독은 그대로
    assert (
        mine.delete("/api/push/subscriptions", {"endpoint": f"{FCM}1"}, format="json").status_code
        == 204
    )
    assert (
        mine.delete("/api/push/subscriptions", {"endpoint": f"{FCM}1"}, format="json").status_code
        == 204
    )
    assert [r.user.intra_id for r in PushSubscriptionRow.objects.all()] == ["staff"]


def test_unsubscribe_works_even_if_push_was_turned_off_meanwhile(settings, vapid):
    client = login()
    client.post("/api/push/subscriptions", body(), format="json")
    settings.VAPID_PRIVATE_KEY = ""
    assert (
        client.delete("/api/push/subscriptions", {"endpoint": f"{FCM}1"}, format="json").status_code
        == 204
    )
    assert PushSubscriptionRow.objects.count() == 0


def test_deleting_a_user_cascades_to_subscriptions(vapid):
    login().post("/api/push/subscriptions", body(), format="json")
    User.objects.filter(intra_id="student").delete()
    assert PushSubscriptionRow.objects.count() == 0


# ── 이벤트 → 알림 → (앱 안 + 푸시) 전체 흐름 ──
class FakeSender:
    def __init__(self, gone=()):
        self.sent, self.gone = [], set(gone)

    def send(self, subscription, payload):
        if subscription.endpoint in self.gone:
            raise SubscriptionGone()
        self.sent.append((subscription.endpoint, payload))


def build_chain(sender):
    """운영 wiring 과 같은 구성(InApp + WebPush)을 별도 버스에 조립한다."""
    channels = [InAppNotifier(), WebPushNotifier(DjangoPushSubscriptionRepository(), sender)]
    bus = InProcessEventDispatcher()
    register_handlers(
        bus, NotificationHandlers(NotificationService(channels), DjangoUserDirectory())
    )
    return bus


def confirmed_event(student_id):
    when = datetime.now(UTC) + timedelta(days=2)
    return MeetingConfirmed(
        meeting_id=7, student_id=student_id, staff_id=0, slot_at=when, location="1층 사무실 앞"
    )


def test_confirmed_meeting_reaches_the_subscribed_device_and_the_in_app_list(vapid):
    student = login("student")
    student.post("/api/push/subscriptions", body(1), format="json")
    sender = FakeSender()
    build_chain(sender).publish(confirmed_event(User.objects.get(intra_id="student").pk))

    ((endpoint, payload),) = sender.sent
    assert endpoint == f"{FCM}1"
    assert payload["title"] == "면담이 확정되었어요" and payload["link"] == "/meeting"
    assert "1층 사무실 앞" in payload["body"]
    assert student.get("/api/notifications").json()["items"][0]["type"] == "meeting_confirmed"


def test_user_without_a_subscription_only_gets_the_in_app_notification(vapid):
    student = login("student")
    sender = FakeSender()
    build_chain(sender).publish(confirmed_event(User.objects.get(intra_id="student").pk))
    assert sender.sent == []
    assert student.get("/api/notifications").json()["unread_count"] == 1


def test_expired_device_is_cleaned_up_but_the_notification_is_still_saved(vapid):
    student = login("student")
    student.post("/api/push/subscriptions", body(1), format="json")
    student.post("/api/push/subscriptions", body(2), format="json")
    sender = FakeSender(gone={f"{FCM}1"})
    build_chain(sender).publish(confirmed_event(User.objects.get(intra_id="student").pk))
    assert [e for e, _ in sender.sent] == [f"{FCM}2"]
    assert list(PushSubscriptionRow.objects.values_list("endpoint", flat=True)) == [f"{FCM}2"]
    assert NotificationRow.objects.count() == 1


def test_a_crashing_push_sender_never_breaks_the_in_app_notification(vapid):
    class Crash:
        def send(self, subscription, payload):
            raise RuntimeError("boom")

    student = login("student")
    student.post("/api/push/subscriptions", body(1), format="json")
    build_chain(Crash()).publish(confirmed_event(User.objects.get(intra_id="student").pk))
    assert NotificationRow.objects.count() == 1
    assert PushSubscriptionRow.objects.count() == 1  # 일시 장애로 구독을 지우지 않는다
