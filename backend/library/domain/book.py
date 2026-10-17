from dataclasses import dataclass

from library.domain.errors import InvalidBook


@dataclass
class Book:
    code: str
    title: str
    category: str
    quantity: int = 1
    author: str = ""
    publisher: str = ""
    isbn: str = ""
    description: str = ""
    cover_url: str = ""
    link_url: str = ""
    pub_date: str = ""
    id: int | None = None

    def __post_init__(self) -> None:
        self.code = self.code.strip()
        self.title = self.title.strip()
        if not self.code:
            raise InvalidBook("도서 코드가 필요합니다")
        if not self.title:
            raise InvalidBook("도서 제목이 필요합니다")
        if self.quantity < 0:
            raise InvalidBook("수량은 0 이상이어야 합니다")
