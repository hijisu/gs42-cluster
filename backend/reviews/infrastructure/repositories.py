from django.db import IntegrityError, transaction
from django.db.models import Avg, Count

from reviews.application.ports import CourseStats
from reviews.domain.course import Course, normalize_intra_id
from reviews.domain.errors import AlreadyReviewed
from reviews.domain.review import Review
from reviews.infrastructure.models import CourseParticipant, CourseRow, ReviewRow


def _course(row: CourseRow) -> Course:
    return Course(
        id=row.pk,
        name=row.name,
        start_date=row.start_date,
        end_date=row.end_date,
        location=row.location,
        intro=row.intro,
        review_deadline=row.review_deadline,
        participants={normalize_intra_id(p.intra_id) for p in row.participants.all()},
    )


def _course_fields(course: Course) -> dict:
    return {
        "name": course.name,
        "start_date": course.start_date,
        "end_date": course.end_date,
        "location": course.location,
        "intro": course.intro,
        "review_deadline": course.review_deadline,
    }


class DjangoCourseRepository:
    @transaction.atomic
    def add(self, course: Course) -> Course:
        course.id = CourseRow.objects.create(**_course_fields(course)).pk
        self._sync_participants(course)
        return course

    @transaction.atomic
    def save(self, course: Course) -> None:
        CourseRow.objects.filter(pk=course.id).update(**_course_fields(course))
        self._sync_participants(course)

    @staticmethod
    def _sync_participants(course: Course) -> None:
        # 참여자를 도메인 집합과 맞춘다: 빠진 사람은 지우고 새 사람은 추가한다(후기는 그대로).
        CourseParticipant.objects.filter(course_id=course.id).exclude(
            intra_id__in=course.participants
        ).delete()
        CourseParticipant.objects.bulk_create(
            [
                CourseParticipant(course_id=course.id, intra_id=i)
                for i in sorted(course.participants)
            ],
            ignore_conflicts=True,
        )

    def list_all(self) -> list[Course]:
        return [_course(r) for r in CourseRow.objects.prefetch_related("participants")]

    def get(self, course_id: int) -> Course | None:
        row = CourseRow.objects.prefetch_related("participants").filter(pk=course_id).first()
        return _course(row) if row else None


def _review(row: ReviewRow) -> Review:
    return Review(
        id=row.pk,
        course_id=row.course_id,
        author_id=row.author_id,
        author_intra_id=row.author.intra_id,
        rating=row.rating,
        good=row.good,
        bad=row.bad,
        recommend_to=row.recommend_to,
        tags=row.tags,
        anonymous=row.anonymous,
        created_at=row.created_at,
    )


class DjangoReviewRepository:
    def add(self, review: Review) -> Review:
        try:
            with transaction.atomic():  # savepoint
                row = ReviewRow.objects.create(
                    course_id=review.course_id,
                    author_id=review.author_id,
                    anonymous=review.anonymous,
                    rating=review.rating,
                    good=review.good,
                    bad=review.bad,
                    recommend_to=review.recommend_to,
                    tags=review.tags,
                )
        except IntegrityError as exc:  # 동시 요청의 중복 작성
            raise AlreadyReviewed("이미 후기를 작성했습니다") from exc
        review.id, review.created_at = row.pk, row.created_at
        return review

    def exists(self, course_id: int, author_id: int) -> bool:
        return ReviewRow.objects.filter(course_id=course_id, author_id=author_id).exists()

    def list_for_course(self, course_id: int) -> list[Review]:
        rows = ReviewRow.objects.filter(course_id=course_id).select_related("author")
        return [_review(r) for r in rows.order_by("-created_at", "-id")]

    def reviewed_course_ids(self, author_id: int) -> set[int]:
        return set(
            ReviewRow.objects.filter(author_id=author_id).values_list("course_id", flat=True)
        )

    def stats_by_course(self) -> dict[int, CourseStats]:
        rows = ReviewRow.objects.values("course_id").annotate(avg=Avg("rating"), n=Count("id"))
        return {r["course_id"]: CourseStats(round(float(r["avg"]), 1), r["n"]) for r in rows}

    def reviewer_intra_ids_by_course(self) -> dict[int, set[str]]:
        result: dict[int, set[str]] = {}
        for course_id, intra_id in ReviewRow.objects.values_list("course_id", "author__intra_id"):
            result.setdefault(course_id, set()).add(normalize_intra_id(intra_id))
        return result
