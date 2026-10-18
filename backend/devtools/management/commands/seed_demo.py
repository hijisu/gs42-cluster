"""시연용 데이터 한 번에 준비. DJANGO_DEBUG=true 에서만 동작하고 여러 번 실행해도 안전하다.

python manage.py seed_demo            # 면담 담당자·가능 시간, 교육과정·후기, 면담 신청·예약 예시
python manage.py seed_demo --reset    # 모의 계정·시연 교육생의 신청·예약·알림을 지우고 다시 만든다

발표 영상용 데이터(운영팀1~5와 모의 staff의 유형별 담당자·성긴 가능 시간, 처리 대기 면담 8건·회의실
요청 6건 등)도 기본으로 함께 만든다. 직접 만든 데이터를 건드리지 않도록 키(교육생·시각·유형 등)로
get_or_create 하고, --reset 때만 시연 계정 데이터와 시연 스태프의 가능 시간을 처음으로 되돌린다.
"""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from accounts.domain.role import Role
from accounts.infrastructure.models import User
from library.infrastructure.models import BookReportRow, BookRow, WishRow
from meetings.infrastructure.models import (
    AvailabilityCustomDay,
    AvailabilitySlot,
    MeetingRequestRow,
    MeetingType,
)
from notifications.infrastructure.models import NotificationRow
from reviews.infrastructure.models import ReviewRow
from rooms.infrastructure.models import Room, RoomBlockRow, RoomReservationRow

KST = ZoneInfo("Asia/Seoul")
MOCK_USERS = ("student", "staff")  # reset 은 이 두 모의 계정과 시연 교육생의 데이터만 지운다
PEERS = ("intra_a", "intra_b", "intra_c", "intra_d", "intra_e")  # 시연용 다른 교육생
DEMO_STAFF = tuple((f"staff{n}", f"운영팀{n}") for n in range(1, 6))
AVAILABILITY_DAYS = 28  # 오늘부터 4주(운영팀 화면에서 설정할 수 있는 범위와 같다)

# 유형별 기본 담당자: 유형마다 담당자가 달라 유형을 바꾸면 희망 시간이 달라진다.
TYPE_STAFF = {
    "freeze": "staff1",
    "other-program": "staff2",
    "dormitory": "staff3",
    "assignment": "staff4",
    "military": "staff5",
    "other": "staff",
}

# 담당자별 가능 시간: (요일 0=월, 시작, 끝). 평일 근무 70칸 중 약 20%(14칸)만 서로 다르게 연다.
AVAILABILITY = {
    "staff1": [
        (0, "10:00", "12:00"),
        (2, "13:00", "15:00"),
        (3, "16:00", "17:00"),
        (4, "14:00", "16:00"),
    ],
    "staff2": [
        (0, "15:00", "17:00"),
        (1, "10:00", "12:00"),
        (3, "13:00", "15:00"),
        (4, "10:00", "11:00"),
    ],
    "staff3": [
        (0, "13:00", "14:00"),
        (1, "14:00", "16:00"),
        (2, "10:00", "12:00"),
        (4, "13:00", "15:00"),
    ],
    "staff4": [
        (1, "15:00", "17:00"),
        (2, "14:00", "15:00"),
        (3, "10:00", "12:00"),
        (4, "15:00", "17:00"),
    ],
    "staff5": [
        (0, "13:00", "15:00"),
        (2, "15:00", "17:00"),
        (3, "14:00", "15:00"),
        (4, "10:00", "12:00"),
    ],
    "staff": [
        (0, "10:00", "11:00"),
        (1, "13:00", "15:00"),
        (2, "11:00", "12:00"),
        (3, "15:00", "17:00"),
        (4, "13:00", "14:00"),
    ],
}

# 면담 신청 예시: (교육생, 유형 코드, 그 담당자의 가능 시간 중 몇 번째, 상태, 내용)
PENDING_MEETINGS = [
    ("intra_a", "freeze", 0, "프리즈 신청 전에 일정과 절차를 확인하고 싶어요."),
    ("intra_b", "freeze", 4, "프리즈 기간 중 과제 제출 방법이 궁금합니다."),
    ("intra_c", "other-program", 0, "타 사업 참여로 출석 인정이 되는지 문의드려요."),
    ("intra_d", "dormitory", 2, "기숙사 퇴실 일정 변경을 상의하고 싶습니다."),
    ("intra_e", "assignment", 1, "과제 제출 기한 연장이 가능한지 궁금해요."),
    ("intra_a", "military", 3, "예비군 훈련 일정과 교육이 겹쳐 상담이 필요합니다."),
    ("intra_c", "other", 0, "기타 문의: 수료 요건을 다시 확인하고 싶어요."),
    ("intra_d", "freeze", 0, "프리즈 관련 급한 문의가 있어요(위 요청과 같은 시간)."),  # 충돌 예시
]

# 회의실 예시(다음 평일 기준 day 번호 1~4): (교육생, 장소 코드, 날, 시작, 끝, 상태, 목적, 인원)
EXTRA_RESERVATIONS = [
    ("intra_c", "universe-large", 1, 14, 16, "approved", "수학 스터디", 8),
    ("intra_d", "multipurpose", 2, 13, 15, "approved", "프로젝트 발표 연습", 5),
    ("intra_e", "universe-small", 2, 10, 12, "approved", "영어 회화 모임", 6),
    ("intra_a", "universe-large", 3, 10, 12, "approved", "코딩 테스트 스터디", 7),
    ("intra_b", "multipurpose", 3, 15, 17, "approved", "팀 회의", 4),
    ("intra_e", "multipurpose", 2, 14, 16, "pending", "멘토링", 3),  # 위 승인 예약과 겹침
    ("intra_c", "universe-large", 2, 15, 17, "pending", "알고리즘 스터디", 6),
    ("intra_d", "universe-small", 3, 13, 15, "pending", "세미나 준비", 5),
    ("intra_a", "multipurpose", 4, 10, 12, "pending", "해커톤 회의", 4),
    ("intra_b", "universe-large", 4, 14, 16, "pending", "발표 리허설", 8),
    ("intra_c", "universe-small", 3, 10, 11, "rejected", "개인 학습", 1),
]


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
        self._seed_showcase(reset=options["reset"])
        self.stdout.write(self.style.SUCCESS("시연 데이터 준비 완료"))

    def _reset(self):
        users = User.objects.filter(intra_id__in=MOCK_USERS + PEERS)
        counts = {
            "면담 신청": MeetingRequestRow.objects.filter(student__in=users).delete()[0],
            "회의실 예약": RoomReservationRow.objects.filter(user__in=users).delete()[0],
            "후기": ReviewRow.objects.filter(
                author__in=users.filter(intra_id__in=MOCK_USERS)
            ).delete()[0],
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

    # ── 발표 영상용 데이터 ──────────────────────────────────────────────

    def _seed_showcase(self, reset):
        staff = self._demo_staff()
        peers = self._peers()
        self._seed_availability(staff, reset)
        self._assign_default_staff(staff, reset)
        self._seed_meeting_requests(staff, peers)
        self._seed_more_reservations(peers)
        self._seed_blocks(staff["staff"])
        self._seed_library(peers)

    def _demo_staff(self):
        staff = {"staff": User.objects.get(intra_id="staff")}
        for login, name in DEMO_STAFF:
            staff[login], _ = User.objects.get_or_create(
                intra_id=login, defaults={"name": name, "role": Role.STAFF.value}
            )
        return staff

    def _peers(self):
        return {
            login: User.objects.get_or_create(
                intra_id=login, defaults={"name": login, "role": Role.STUDENT.value}
            )[0]
            for login in PEERS
        }

    def _seed_availability(self, staff, reset):
        """담당자마다 오늘부터 4주 평일을 '직접 저장한 날'로 만들어 서로 다른 성긴 시간을 연다.

        이미 직접 저장한 날(화면에서 바꾼 값)은 그대로 두고, --reset 일 때만 처음 상태로 되돌린다.
        """
        today = timezone.localdate()
        last = today + timedelta(days=AVAILABILITY_DAYS - 1)
        window = (
            datetime.combine(today, time.min, tzinfo=KST),
            datetime.combine(last + timedelta(days=1), time.min, tzinfo=KST),
        )
        if reset:
            ids = [u.pk for u in staff.values()]
            AvailabilityCustomDay.objects.filter(
                staff_id__in=ids, day__gte=today, day__lte=last
            ).delete()
            AvailabilitySlot.objects.filter(
                staff_id__in=ids, start_at__gte=window[0], start_at__lt=window[1]
            ).delete()
        created_days = 0
        for login, user in staff.items():
            for offset in range(AVAILABILITY_DAYS):
                day = today + timedelta(days=offset)
                if day.weekday() >= 5:
                    continue
                _, created = AvailabilityCustomDay.objects.get_or_create(staff=user, day=day)
                if not created:
                    continue
                created_days += 1
                AvailabilitySlot.objects.bulk_create(
                    [AvailabilitySlot(staff=user, start_at=at) for at in pattern_slots(login, day)],
                    ignore_conflicts=True,
                )
        self.stdout.write(
            f"가능 시간 {created_days}일 생성(스태프 {len(staff)}명, 4주, 각자 약 20%)"
        )

    def _assign_default_staff(self, staff, reset):
        """유형별 기본 담당자를 서로 다르게 지정한다(담당자 없음·모의 staff·--reset 일 때만)."""
        changed = 0
        for meeting_type in MeetingType.objects.select_related("default_staff"):
            target = staff.get(TYPE_STAFF.get(meeting_type.code, ""))
            current = meeting_type.default_staff
            if target is None or current == target:
                continue
            if reset or current is None or current.intra_id == "staff":
                meeting_type.default_staff = target
                meeting_type.save(update_fields=["default_staff"])
                changed += 1
        self.stdout.write(f"유형별 기본 담당자 {changed}건 지정")

    def _seed_meeting_requests(self, staff, peers):
        """처리 대기 8건(충돌 1쌍 포함), 시간 조율 중 1건, 확정 2건, 지난 1건."""
        types = {t.code: t for t in MeetingType.objects.all()}
        slots = {login: upcoming_slots(login) for login in AVAILABILITY}
        now = timezone.now()
        created = 0

        def make(student, code, at, status, content, **extra):
            nonlocal created
            row, was_created = MeetingRequestRow.objects.get_or_create(
                student=peers[student],
                type=types[code],
                slot_at=at,
                defaults={
                    "content": content,
                    "notify_slack": True,
                    "status": status,
                    "staff": staff[TYPE_STAFF[code]],
                    **extra,
                },
            )
            if was_created:
                created += 1
                # 접수 시각을 흩어 놓아 목록이 자연스럽게 보이게 한다.
                MeetingRequestRow.objects.filter(pk=row.pk).update(
                    created_at=now - timedelta(minutes=15 * (created + 1))
                )

        for student, code, index, content in PENDING_MEETINGS:
            at = slots[TYPE_STAFF[code]][index]
            make(student, code, at, "pending", content)
        other = slots["staff2"]
        make(
            "intra_e",
            "other-program",
            other[2],
            "proposed",
            "타 사업 참여 일정 상담을 받고 싶어요.",
            proposed_at=other[5],
            location="1층 상담실",
            staff_note="요청하신 시간에 선약이 있어 다른 시간을 제안드려요.",
        )
        make(
            "intra_b", "dormitory", slots["staff3"][6], "confirmed", "기숙사 호실 변경 문의입니다.",
            location="1층 사무실 앞",
        )  # fmt: skip
        make(
            "intra_d", "military", slots["staff5"][6], "confirmed", "예비군 증빙 서류 문의입니다.",
            location="2층 상담실",
        )  # fmt: skip
        past = previous_weekday_slot()
        make("intra_a", "freeze", past, "completed", "지난 면담입니다.", location="1층 사무실 앞")
        self.stdout.write(f"면담 신청 예시 {created}건 생성(이미 있으면 건너뜀)")

    def _seed_more_reservations(self, peers):
        rooms = {r.code: r for r in Room.objects.all()}
        if not rooms:
            return
        base = next_weekday(timezone.localdate())
        days = {1: base}
        for number in (2, 3, 4):
            days[number] = next_weekday(days[number - 1])
        created = 0
        for login, code, number, start, end, status, purpose, headcount in EXTRA_RESERVATIONS:
            day = days[number]
            _, was_created = RoomReservationRow.objects.get_or_create(
                user=peers[login],
                room=rooms[code],
                start_at=datetime.combine(day, time(start), tzinfo=KST),
                defaults={
                    "requested_room": rooms[code],
                    "end_at": datetime.combine(day, time(end), tzinfo=KST),
                    "purpose": purpose,
                    "headcount": headcount,
                    "status": status,
                    "reject_reason": "교육 일정과 겹쳐 사용할 수 없어요."
                    if status == "rejected"
                    else "",
                },
            )
            created += was_created
        self.stdout.write(f"회의실 예약 예시 {created}건 추가 생성")

    def _seed_blocks(self, staff_user):
        """주기적인 교육 활동 예시: 매주 토요일 유니버스룸(대)·평일 저녁 유니버스룸(소)."""
        rooms = {r.code: r for r in Room.objects.all()}
        if not rooms:
            return
        today = timezone.localdate()
        saturday = today + timedelta((5 - today.weekday()) % 7 or 7)
        weekday = next_weekday(today)
        until = today + timedelta(weeks=8)
        specs = [
            ("universe-large", saturday, 10, 12, "수학 교육", "weekly", [5]),
            ("universe-small", weekday, 18, 21, "영어 교육", "weekdays", []),
        ]
        created = 0
        for code, day, start, end, reason, repeat, weekdays in specs:
            if code not in rooms:
                continue
            _, was_created = RoomBlockRow.objects.get_or_create(
                room=rooms[code],
                reason=reason,
                repeat=repeat,
                defaults={
                    "start_at": datetime.combine(day, time(start), tzinfo=KST),
                    "end_at": datetime.combine(day, time(end), tzinfo=KST),
                    "weekdays": weekdays,
                    "until": until,
                    "created_by": staff_user,
                },
            )
            created += was_created
        self.stdout.write(f"예약 차단 예시 {created}건 생성")

    def _seed_library(self, peers):
        """운영 홈의 처리 대기에 도서가 비지 않도록 희망 도서·분실 신고 예시(도서가 있을 때만)."""
        book = BookRow.objects.order_by("code").first()
        wishes = [
            ("intra_a", "리팩터링 2판", "마틴 파울러", "코드 품질을 높이는 방법을 배우고 싶어요."),
            (
                "intra_b",
                "도메인 주도 설계",
                "에릭 에반스",
                "프로젝트 구조를 설계할 때 참고하고 싶습니다.",
            ),
        ]
        created = 0
        for login, title, author, reason in wishes:
            _, was_created = WishRow.objects.get_or_create(
                user=peers[login], title=title, defaults={"author": author, "reason": reason}
            )
            created += was_created
        if book is not None:
            _, was_created = BookReportRow.objects.get_or_create(
                book=book, user=peers["intra_c"], kind="lost", defaults={"detail": ""}
            )
            created += was_created
        self.stdout.write(f"도서 희망·신고 예시 {created}건 생성")


def pattern_slots(login, day):
    """그 담당자가 day(KST 날짜)에 여는 30분 칸 시작 시각 목록."""
    slots = []
    for weekday, start, end in AVAILABILITY[login]:
        if day.weekday() != weekday:
            continue
        current = datetime.combine(day, time.fromisoformat(start), tzinfo=KST)
        closing = datetime.combine(day, time.fromisoformat(end), tzinfo=KST)
        while current < closing:
            slots.append(current)
            current += timedelta(minutes=30)
    return slots


def upcoming_slots(login):
    """내일부터 4주 안에서 그 담당자가 여는 칸(시간순). 면담 신청 예시의 희망 시각으로 쓴다."""
    start = timezone.localdate() + timedelta(days=1)
    found = []
    for offset in range(AVAILABILITY_DAYS):
        found.extend(pattern_slots(login, start + timedelta(days=offset)))
    return found


def previous_weekday_slot():
    day = timezone.localdate() - timedelta(days=1)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return datetime.combine(day, time(10), tzinfo=KST)
