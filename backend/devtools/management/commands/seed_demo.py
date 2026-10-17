"""시연용 데이터 한 번에 준비. DJANGO_DEBUG=true 에서만 동작하고 여러 번 실행해도 안전하다.

python manage.py seed_demo            # 면담 슬롯·기본 담당자, 교육과정·후기, 예약 예시
python manage.py seed_demo --reset    # 모의 계정(student/staff)의 신청·예약·후기·알림 초기화
"""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from accounts.infrastructure.models import User
from meetings.infrastructure.models import MeetingRequestRow
from notifications.infrastructure.models import NotificationRow
from reviews.infrastructure.models import ReviewRow
from rooms.infrastructure.models import Room, RoomReservationRow

KST = ZoneInfo("Asia/Seoul")
MOCK_USERS = ("student", "staff")  # reset 은 이 두 모의 계정의 데이터만 지운다


def next_weekday(day):
    day += timedelta(days=1)
    while day.weekday() >= 5:
        day += timedelta(days=1)
    return day


class Command(BaseCommand):
    help = "시연용 데이터 준비(면담 슬롯, 교육과정·후기, 예약 예시). --reset 은 모의 계정만 초기화."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true", help="student/staff 모의 계정의 데이터 초기화"
        )
        parser.add_argument("--days", type=int, default=7, help="면담 슬롯을 열 일수(기본 7)")

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("DJANGO_DEBUG=true에서만 실행할 수 있습니다")
        if options["reset"]:
            self._reset()
        call_command("seed_meeting_demo", days=options["days"], stdout=self.stdout)
        call_command("seed_review_demo", stdout=self.stdout)
        self._seed_reservations()
        self.stdout.write(self.style.SUCCESS("시연 데이터 준비 완료"))

    def _reset(self):
        users = User.objects.filter(intra_id__in=MOCK_USERS)
        counts = {
            "면담 신청": MeetingRequestRow.objects.filter(student__in=users).delete()[0],
            "회의실 예약": RoomReservationRow.objects.filter(user__in=users).delete()[0],
            "후기": ReviewRow.objects.filter(author__in=users).delete()[0],
            "알림": NotificationRow.objects.filter(user__in=users).delete()[0],
        }
        self.stdout.write("초기화: " + ", ".join(f"{k} {v}건" for k, v in counts.items()))

    def _seed_reservations(self):
        """다음 평일에 '승인된 예약 1건 + 겹치는 대기 요청 1건 + 다른 장소 대기 1건'을 만든다."""
        peers = {u.intra_id: u for u in User.objects.filter(intra_id__in=("intra_a", "intra_b"))}
        rooms = {r.code: r for r in Room.objects.all()}
        if len(peers) < 2 or not rooms:
            self.stdout.write("예약 예시를 건너뜀(교육생 예시 계정 또는 장소가 없음)")
            return
        day = next_weekday(timezone.localdate())

        def at(hour):
            return datetime.combine(day, time(hour), tzinfo=KST)

        samples = [
            ("intra_a", "multipurpose", 10, 12, "approved", "팀 회의"),
            (
                "intra_b",
                "multipurpose",
                11,
                13,
                "pending",
                "프로젝트 회의",
            ),  # 위와 겹침 → 충돌 표시
            ("intra_b", "universe-small", 15, 17, "pending", "스터디"),
        ]
        created = 0
        for login, code, start, end, status, purpose in samples:
            _, was_created = RoomReservationRow.objects.get_or_create(
                user=peers[login],
                room=rooms[code],
                start_at=at(start),
                defaults={
                    "requested_room": rooms[code],
                    "end_at": at(end),
                    "purpose": purpose,
                    "headcount": 3,
                    "status": status,
                },
            )
            created += was_created
        self.stdout.write(f"예약 예시 {created}건 생성({day:%m.%d} 기준, 이미 있으면 건너뜀)")
