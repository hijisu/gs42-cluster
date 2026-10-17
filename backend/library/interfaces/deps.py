from library.application import usecases as uc
from library.infrastructure.repositories import (
    DjangoBookRepository,
    DjangoReportRepository,
    DjangoWishRepository,
)


def search_books() -> uc.SearchBooksUseCase:
    return uc.SearchBooksUseCase(DjangoBookRepository())


def get_book() -> uc.GetBookUseCase:
    return uc.GetBookUseCase(DjangoBookRepository())


def create_report() -> uc.CreateReportUseCase:
    return uc.CreateReportUseCase(DjangoBookRepository(), DjangoReportRepository())


def create_wish() -> uc.CreateWishUseCase:
    return uc.CreateWishUseCase(DjangoWishRepository())


def my_requests() -> uc.ListMyLibraryRequestsUseCase:
    return uc.ListMyLibraryRequestsUseCase(DjangoReportRepository(), DjangoWishRepository())


def list_reports() -> uc.ListReportsUseCase:
    return uc.ListReportsUseCase(DjangoReportRepository())


def resolve_report() -> uc.ResolveReportUseCase:
    return uc.ResolveReportUseCase(DjangoReportRepository())


def list_wishes() -> uc.ListWishesUseCase:
    return uc.ListWishesUseCase(DjangoWishRepository())


def update_wish() -> uc.UpdateWishUseCase:
    return uc.UpdateWishUseCase(DjangoWishRepository())


def create_book() -> uc.CreateBookUseCase:
    return uc.CreateBookUseCase(DjangoBookRepository())


def update_book() -> uc.UpdateBookUseCase:
    return uc.UpdateBookUseCase(DjangoBookRepository())


def delete_book() -> uc.DeleteBookUseCase:
    return uc.DeleteBookUseCase(DjangoBookRepository())


def import_books() -> uc.ImportBooksUseCase:
    return uc.ImportBooksUseCase(DjangoBookRepository())
