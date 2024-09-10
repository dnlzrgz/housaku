from sqlalchemy import update
from sqlalchemy.orm import Session
from housaku.models import Doc, Posting, Word


class Repository[T: (Doc, Posting, Word)]:
    def __init__(self, session: Session, model) -> None:
        self.session = session
        self.model = model

    def add(self, entity: T) -> T:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)

        return entity

    def add_in_batch(self, entities: list[T]) -> None:
        self.session.add_all(entities)
        self.session.commit()

    def get(self, id: int) -> T | None:
        return self.session.get(self.model, id)

    def get_by_attributes(self, **kwargs) -> T | None:
        return self.session.query(self.model).filter_by(**kwargs).one_or_none()

    def get_all(self) -> list[T]:
        return self.session.query(self.model).all()

    def get_all_by_attributes(self, **kwargs) -> list[T] | None:
        return self.session.query(self.model).filter_by(**kwargs).all()

    def update(self, id: int, **kwargs) -> None:
        stmt = update(self.model).where(self.model.id == id).values(**kwargs)
        self.session.execute(stmt)
        self.session.commit()

    def delete(self, id: int) -> None:
        entity = self.session.get(self.model, id)
        if entity:
            self.session.delete(entity)
            self.session.commit()
            return entity


class DocRepository(Repository[Doc]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Doc)


class PostingRepository(Repository[Posting]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Posting)


class WordRepository(Repository[Word]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Word)
