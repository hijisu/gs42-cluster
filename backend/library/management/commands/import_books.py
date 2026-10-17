import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from library.domain.errors import InvalidBook
from library.interfaces import deps

DEFAULT_FILE = Path(__file__).resolve().parents[2] / "data" / "books.json"


class Command(BaseCommand):
    help = "42gslib 도서 목록(JSON)을 가져온다. 도서 코드 기준 upsert라 여러 번 실행해도 안전하다."

    def add_arguments(self, parser):
        parser.add_argument("--file", default=str(DEFAULT_FILE), help="도서 JSON 경로")

    def handle(self, *args, **options):
        path = Path(options["file"])
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise CommandError(f"도서 파일을 읽을 수 없습니다: {exc}") from exc
        if not isinstance(rows, list):
            raise CommandError("도서 파일은 JSON 배열이어야 합니다")
        try:
            created, updated = deps.import_books().execute(rows)
        except InvalidBook as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(f"도서 가져오기 완료: 새로 {created}종, 갱신 {updated}종")
        )
