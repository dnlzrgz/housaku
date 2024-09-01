from sqlalchemy import JSON, ForeignKey, Text, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Doc(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    uri: Mapped[str] = mapped_column(nullable=False, unique=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    properties: Mapped[dict] = mapped_column(JSON, nullable=True)

    postings: Mapped[list["Posting"]] = relationship(back_populates="doc")

    def __repr__(self) -> str:
        return f"Doc(id={self.id!r}, uri={self.uri!r})"


class Posting(Base):
    __tablename__ = "postings"

    id: Mapped[int] = mapped_column(primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    doc_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    doc: Mapped["Doc"] = relationship(back_populates="postings")

    word_id: Mapped[int] = mapped_column(ForeignKey("words.id"))
    word: Mapped["Word"] = relationship(back_populates="postings")

    def __repr__(self) -> str:
        return (
            f"Posting(id={self.id!r}, doc_id={self.doc_id!r}, word_id={self.word_id!r})"
        )


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(primary_key=True)
    word: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
    )

    postings: Mapped[list["Posting"]] = relationship(back_populates="word")

    def __repr__(self) -> str:
        return f"Word(id={self.id!r}, word={self.word!r})"
