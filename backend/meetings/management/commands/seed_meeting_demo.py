"""개발용: 모의 운영팀 계정을 기본 담당자로 지정하고 앞으로 며칠의 면담 슬롯을 연다."""

from datetime import datetime, time, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from accounts.domain.role import Role
from accounts.infrastructure.models import User
from meetings.infrastructure.models import AvailabilitySlot, MeetingType

HOURS = (10, 11, 13, 14, 15, 16)


class Command(BaseCommand):
    help = "개발용 면담 슬롯 시드 (DJANGO_DEBUG=true에서만). 여러 번 실행해도 안전하다."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=7)

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("DJANGO_DEBUG=true에서만 실행할 수 있습니다")
        staff, _ = User.objects.get_or_create(
            intra_id="staff", defaults={"name": "모의 운영팀", "role": Role.STAFF.value}
        )
        MeetingType.objects.filter(default_staff__isnull=True).update(default_staff=staff)
        tz = timezone.get_current_timezone()
        today = timezone.localdate()
        created = 0
        for offset in range(options["days"]):
            day = today + timedelta(days=offset)
            if day.weekday() >= 5:
                continue
            for hour in HOURS:
                start = datetime.combine(day, time(hour), tzinfo=tz)
                _, was_created = AvailabilitySlot.objects.get_or_create(staff=staff, start_at=start)
                created += was_created
        self.stdout.write(f"슬롯 {created}개 생성, 기본 담당자: {staff.intra_id}")
