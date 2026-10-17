"""개발용: 교육과정 3개와 참여자·후기 예시를 만든다(DJANGO_DEBUG=true에서만, 반복 실행 안전)."""

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from accounts.domain.role import Role
from accounts.infrastructure.models import User
from reviews.infrastructure.models import CourseParticipant, CourseRow, ReviewRow

# (과정명, 장소, 종료 여부): 상태는 날짜로 계산된다. 진행 중 과정은 기간에 오늘이 든다.
COURSES = [
    ("경북 특화형 데이터센터 기초과정", "유니버스룸", True),
    ("서울대학교 파이썬 AI 교육", "온라인", True),
    ("글로벌 기업가 정신 및 AI 몰입 프로그램", "유니버스룸", False),
]


class Command(BaseCommand):
    help = "개발용 교육과정·후기 시드. 모의 교육생(student)을 모든 과정의 참여자로 등록한다."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("DJANGO_DEBUG=true에서만 실행할 수 있습니다")
        today = timezone.localdate()
        peers = [
            User.objects.get_or_create(
                intra_id=login, defaults={"name": login, "role": Role.STUDENT.value}
            )[0]
            for login in ("intra_a", "intra_b")
        ]
        for order, (name, location, ended) in enumerate(COURSES):
            start = today - timedelta(days=30 * (len(COURSES) - order) if ended else 3)
            course, _ = CourseRow.objects.get_or_create(
                name=name,
                defaults={
                    "start_date": start,
                    "end_date": start + timedelta(days=9),
                    "location": location,
                    "intro": f"{name} 소개",
                    "review_deadline": today + timedelta(days=14) if ended else None,
                },
            )
            for login in ("student", "intra_a", "intra_b"):
                CourseParticipant.objects.get_or_create(course=course, intra_id=login)
            if ended:
                for i, peer in enumerate(peers):
                    ReviewRow.objects.get_or_create(
                        course=course,
                        author=peer,
                        defaults={
                            "anonymous": i == 0,
                            "rating": 5 - i,
                            "title": f"{name} 후기 {i + 1}",
                            "good": "실습 위주라 좋았어요.",
                            "bad": "복습 시간이 더 있었으면 좋겠어요.",
                            "recommend_to": "입문자",
                            "tags": ["입문", "실습 위주"],
                        },
                    )
        self.stdout.write("교육과정 3개, 참여자(student, intra_a, intra_b), 후기 예시 생성")
