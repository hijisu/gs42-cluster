"""개발용: 모의 운영팀 계정을 면담 기본 담당자로 지정한다(가능 시간은 기본값이 적용된다)."""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from accounts.domain.role import Role
from accounts.infrastructure.models import User
from meetings.infrastructure.models import MeetingType


class Command(BaseCommand):
    help = "개발용 면담 슬롯 시드 (DJANGO_DEBUG=true에서만). 여러 번 실행해도 안전하다."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=7, help="(사용하지 않음, 호환용)")

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("DJANGO_DEBUG=true에서만 실행할 수 있습니다")
        staff, _ = User.objects.get_or_create(
            intra_id="staff", defaults={"name": "모의 운영팀", "role": Role.STAFF.value}
        )
        MeetingType.objects.filter(default_staff__isnull=True).update(default_staff=staff)
        # 가능 시간은 모든 스태프에게 기본값(평일 10~12·13~17시)이 적용되므로 슬롯을 만들지 않는다.
        self.stdout.write(f"기본 담당자: {staff.intra_id} (가능 시간: 기본값 평일 10~12·13~17시)")
