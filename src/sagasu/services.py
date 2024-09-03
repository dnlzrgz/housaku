from sqlalchemy import select
from sqlalchemy.orm.session import Session
from sagasu.models import Doc, Posting, Word


class SearchService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def search(self, tokens: list[str]) -> list[str] | None:
        results = (
            self.session.execute(
                select(Doc.uri)
                .join(Posting)
                .join(Word)
                .where(Word.word.in_(tokens))
                .distinct()
            )
            .scalars()
            .all()
        )

        return results
