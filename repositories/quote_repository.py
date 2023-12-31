from typing import Optional

from sqlmodel import Session, or_, select, desc

from models import Author, Book, BookAuthorLink, Quote

from .base_repository import BaseRepository
from .enums import QuoteOrder


class QuoteRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__(Quote)

    def get_by_quote(self, session: Session, quote: str) -> Quote | None:
        stmt = select(self.model_type).where(self.model_type.quote == quote)
        return session.exec(stmt).first()

    def add(self, session: Session, quote: Quote) -> None:
        session.add(quote)

    def update(
        self,
        session: Session,
        id: int,
        new_text: str | None = None,
        new_book: Book | None = None,
        new_fav: bool | None = None,
    ) -> None:
        stmt = select(self.model_type).where(self.model_type.id == id)
        results = session.exec(stmt)
        original_quote = results.one()

        if new_text is not None:
            original_quote.quote = new_text

        if new_book is not None:
            original_quote.book = new_book
            original_quote.book_id = new_book.id

        if new_fav is not None:
            original_quote.fav = new_fav

    def list(
        self,
        session: Session,
        words: Optional[list[str]] = None,
        book_id: Optional[int] = None,
        author_id: Optional[int] = None,
        fav: Optional[bool] = None,
        order_by: Optional[QuoteOrder] = QuoteOrder.quote,
        reverse_order: Optional[bool] = False,
        limit: Optional[int] = None,
    ) -> list[Quote]:
        stmt = select(
            self.model_type,
            Book,
            Author,
        ).where(self.model_type.book_id == Book.id)

        stmt = stmt.join(
            BookAuthorLink, self.model_type.book_id == BookAuthorLink.book_id
        )
        stmt = stmt.join(Author, Author.id == BookAuthorLink.author_id)

        if words is not None:
            quote_conditions = [
                self.model_type.quote.ilike(f"%{word}%") for word in words
            ]
            stmt = stmt.where(or_(*quote_conditions))

        if book_id is not None:
            stmt = stmt.where(self.model_type.id == book_id)

        if author_id is not None:
            stmt = stmt.where(Author.id == author_id)

        if fav is not None:
            stmt = stmt.where(self.model_type.fav == fav)

        order_column = self.model_type.quote
        if order_by == QuoteOrder.author:
            order_column = Author.name
        elif order_by == QuoteOrder.book:
            order_column = Book.title
        elif order_by == QuoteOrder.id:
            order_column = self.model_type.id

        stmt = (
            stmt.order_by(desc(order_column))
            if reverse_order
            else stmt.order_by(order_column)
        )

        if limit is not None:
            stmt = stmt.limit(limit)

        result = session.exec(stmt)
        return result.all()
