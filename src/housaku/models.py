from sqlalchemy import JSON, Float, ForeignKey, Text, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Doc(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    uri: Mapped[str] = mapped_column(nullable=False, unique=True)
    content: Mapped[str] = mapped_column(Text, nullable=True)
    properties: Mapped[dict] = mapped_column(JSON, nullable=True)

    postings: Mapped[list["Posting"]] = relationship(back_populates="doc")

    def __repr__(self) -> str:
        return f"Doc(id={self.id!r}, uri={self.uri!r})"


class Posting(Base):
    __tablename__ = "postings"

    id: Mapped[int] = mapped_column(primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    tf: Mapped[float] = mapped_column(Float, default=0, nullable=False)

    doc_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    doc: Mapped["Doc"] = relationship(back_populates="postings")

    word_id: Mapped[int] = mapped_column(ForeignKey("words.id"), index=True)
    word: Mapped["Word"] = relationship(back_populates="postings")

    def __repr__(self) -> str:
        return f"Posting(id={self.id!r}, doc_id={self.doc_id!r}, word_id={self.word_id!r}, count={self.count!r}, tf={self.tf!r})"


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(primary_key=True)
    word: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
        index=True,
    )

    postings: Mapped[list["Posting"]] = relationship(back_populates="word")

    def __repr__(self) -> str:
        return (
            f"Word(id={self.id!r}, word={self.word!r}, postings={len(self.postings)!r})"
        )
