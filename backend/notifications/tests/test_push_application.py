"""웹 푸시 채널 유스케이스 테스트: DB 없이 가짜 저장소·전송기 사용."""

import json
import logging

import pytest

from notifications.application.push import (
    SubscribePushUseCase,
    SubscriptionGone,
    UnsubscribePushUseCase,
    WebPushNotifier,
    push_payload,
)
from notifications.domain.notification import Notification, NotificationType
from notifications.domain.push import InvalidSubscription, PushSubscription

FCM = "https://fcm.googleapis.com/fcm/send/"
KEY = "BEl62iUYgUivxIkv"


class Repo:
    def __init__(self):
        self.rows: dict[str, PushSubscription] = {}

    def upsert(self, s):
        s.id = s.id or len(self.rows) + 1
        self.rows[s.endpoint] = s
        return s

    def list_for_user(self, user_id):
        return [s for s in self.rows.values() if s.user_id == user_id]

    def delete(self, user_id, endpoint):
        row = self.rows.get(endpoint)
        if row and row.user_id == user_id:
            del self.rows[endpoint]
            return True
        return False

    def delete_endpoint(self, endpoint):
        self.rows.pop(endpoint, None)


class Sender:
    def __init__(self, behavior=None):
        self.sent: list[tuple[str, dict]] = []
        self.behavior = behavior or {}

    def send(self, subscription, payload):
        action = self.behavior.get(subscription.endpoint)
        if action == "gone":
            raise SubscriptionGone()
        if action == "boom":
            raise RuntimeError("push service down")
        self.sent.append((subscription.endpoint, payload))


def sub(repo, n, user=1):
    return repo.upsert(PushSubscription.create(user, f"{FCM}{n}", KEY, KEY))


def note(user=1):
    return Notification(
        user_id=user,
        type=NotificationType.RESERVATION_APPROVED,
        title="회의실 예약이 확정되었어요",
        body="다목적회의실 · 10.22 10:00–12:00",
        link="/room",
        data={"reservation_id": 5},
    )


def test_payload_has_exactly_what_the_service_worker_reads_plus_type():
    payload = push_payload(note())
    assert payload == {
        "title": "회의실 예약이 확정되었어요",
        "body": "다목적회의실 · 10.22 10:00–12:00",
        "link": "/room",
        "type": "reservation_approved",
    }
    json.dumps(payload, ensure_ascii=False)  # JSON 직렬화 가능


def test_user_without_subscription_gets_no_push_and_no_error():
    repo, sender = Repo(), Sender()
    WebPushNotifier(repo, sender).send(note())
    assert sender.sent == []


def test_every_device_of_the_user_receives_the_push():
    repo, sender = Repo(), Sender()
    sub(repo, 1)
    sub(repo, 2)
    sub(repo, 3, user=2)  # 다른 사용자 기기에는 가지 않는다
    WebPushNotifier(repo, sender).send(note(user=1))
    assert sorted(e for e, _ in sender.sent) == [f"{FCM}1", f"{FCM}2"]


def test_gone_subscription_is_deleted_and_others_still_receive():
    repo = Repo()
    sub(repo, 1)
    sub(repo, 2)
    sender = Sender({f"{FCM}1": "gone"})
    WebPushNotifier(repo, sender).send(note())
    assert [e for e, _ in sender.sent] == [f"{FCM}2"]
    assert f"{FCM}1" not in repo.rows and f"{FCM}2" in repo.rows


def test_one_failing_device_does_not_block_the_rest_and_keeps_its_subscription(caplog):
    repo = Repo()
    sub(repo, 1)
    sub(repo, 2)
    sender = Sender({f"{FCM}1": "boom"})
    with caplog.at_level(logging.ERROR):
        WebPushNotifier(repo, sender).send(note())
    assert [e for e, _ in sender.sent] == [f"{FCM}2"]
    assert f"{FCM}1" in repo.rows  # 일시 장애로는 구독을 지우지 않는다
    assert "웹 푸시 전송 실패" in caplog.text


def test_subscribe_validates_and_upserts_by_endpoint():
    repo = Repo()
    uc = SubscribePushUseCase(repo)
    first = uc.execute(1, f"{FCM}abc", KEY, KEY)
    again = uc.execute(1, f"{FCM}abc", "BEl62iUYgUivxIkw", KEY)
    assert (
        len(repo.rows) == 1
        and again.p256dh == "BEl62iUYgUivxIkw"
        and first.endpoint == again.endpoint
    )
    with pytest.raises(InvalidSubscription):
        uc.execute(1, "https://internal.example.com/x", KEY, KEY)
    assert len(repo.rows) == 1


def test_unsubscribe_is_idempotent_and_cannot_remove_someone_elses():
    repo = Repo()
    sub(repo, 1, user=1)
    uc = UnsubscribePushUseCase(repo)
    uc.execute(2, f"{FCM}1")  # 남의 구독: 아무 일도 없다
    assert f"{FCM}1" in repo.rows
    uc.execute(1, f"{FCM}1")
    uc.execute(1, f"{FCM}1")  # 두 번째도 오류 없음
    assert repo.rows == {}
