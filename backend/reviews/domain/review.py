"""후기. 익명 후기의 작성자 숨김은 public_view()가 책임진다."""

from dataclasses import dataclass, field
from datetime import datetime

from reviews.domain.errors import InvalidReview, NotReviewAuthor

MAX_TAGS = 5
MAX_TAG_LENGTH = 20


def normalize_tags(tags: list[str]) -> list[str]:
    """앞의 '#'과 공백을 떼고 빈 값·중복을 제거한다(순서 유지)."""
    seen: dict[str, None] = {}
    for tag in tags:
        cleaned = tag.strip().lstrip("#").strip()
        if cleaned:
            seen.setdefault(cleaned, None)
    return list(seen)


@dataclass(frozen=True)
class PublicReview:
    """API로 내려가는 후기. 익명이면 작성자 정보가 아예 없다."""

    id: int
    course_id: int
    rating: int
    good: str
    bad: str
    recommend_to: str
    tags: list[str]
    anonymous: bool
    author_intra_id: str | None
    created_at: datetime | None


@dataclass
class Review:
    course_id: int
    author_id: int
    author_intra_id: str
    rating: int
    good: str = ""
    bad: str = ""
    recommend_to: str = ""
    tags: list[str] = field(default_factory=list)
    anonymous: bool = False
    created_at: datetime | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        self.tags = normalize_tags(self.tags)
        if not 1 <= self.rating <= 5:
            raise InvalidReview("만족도는 1~5 사이여야 합니다")
        if len(self.tags) > MAX_TAGS or any(len(t) > MAX_TAG_LENGTH for t in self.tags):
            raise InvalidReview(f"태그는 {MAX_TAGS}개 이하, 각 {MAX_TAG_LENGTH}자 이하여야 합니다")

    def ensure_author(self, editor_id: int) -> None:
        if editor_id != self.author_id:
            raise NotReviewAuthor("후기는 작성자만 수정할 수 있습니다")

    def edit(self, editor_id: int, **changes) -> None:
        """작성자 본인만 고친다(삭제 없음). 검증에 실패하면 바뀌지 않는다."""
        self.ensure_author(editor_id)
        allowed = {"rating", "good", "bad", "recommend_to", "tags", "anonymous"}
        unknown = set(changes) - allowed
        if unknown:
            raise InvalidReview(f"수정할 수 없는 항목입니다: {', '.join(sorted(unknown))}")
        before = {name: getattr(self, name) for name in changes}
        for name, value in changes.items():
            setattr(self, name, value)
        try:
            self._validate()
        except InvalidReview:
            for name, value in before.items():
                setattr(self, name, value)
            raise

    def public_view(self) -> PublicReview:
        return PublicReview(
            id=self.id,
            course_id=self.course_id,
            rating=self.rating,
            good=self.good,
            bad=self.bad,
            recommend_to=self.recommend_to,
            tags=list(self.tags),
            anonymous=self.anonymous,
            author_intra_id=None if self.anonymous else self.author_intra_id,
            created_at=self.created_at,
        )
