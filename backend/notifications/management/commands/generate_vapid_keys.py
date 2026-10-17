"""웹 푸시용 VAPID 키 한 쌍을 만든다. 출력된 값을 .env 의 VAPID_* 에 직접 넣는다."""

from django.core.management.base import BaseCommand

from notifications.infrastructure.vapid import generate_keys


class Command(BaseCommand):
    help = "VAPID 키 쌍을 생성해 출력한다(저장하지 않음). 개인키는 .env 에만 둔다."

    def handle(self, *args, **options):
        public, private = generate_keys()
        self.stdout.write(f"VAPID_PUBLIC_KEY={public}")
        self.stdout.write(f"VAPID_PRIVATE_KEY={private}")
        self.stderr.write(
            "위 두 줄을 .env 에 붙여 넣으세요. "
            "VAPID_PRIVATE_KEY 는 비밀값입니다(커밋·채팅·이슈 금지)."
        )
