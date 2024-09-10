import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from housaku.db import init_db
from housaku.models import Base, Doc, Posting, Word
from housaku.repositories import DocRepository, PostingRepository, WordRepository
from housaku.search import search


@pytest.fixture(scope="function")
def session():
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture
def doc_repo(session):
    return DocRepository(session)


@pytest.fixture
def posting_repo(session):
    return PostingRepository(session)


@pytest.fixture
def word_repo(session):
    return WordRepository(session)


def test_search_no_docs(session):
    result = search(session, ["tdd"])
    assert result == []


def test_search_no_matching_words(session, doc_repo):
    doc_repo.add(Doc(uri="test1"))
    doc_repo.add(Doc(uri="test2"))
    tokens = ["nonexistent", "words"]

    results = search(session, tokens)
    assert results == []


def test_search_empty_token_list(session, doc_repo):
    doc_repo.add(Doc(uri="test1"))
    doc_repo.add(Doc(uri="test2"))

    results = search(session, [])
    assert results == []


def test_search_two_docs(session, doc_repo, posting_repo, word_repo):
    doc1_in_db = doc_repo.add(Doc(uri="test1"))
    doc_repo.add(Doc(uri="test2"))
    tokens = ["tdd", "does", "not", "work"]

    for token in tokens:
        word_in_db = word_repo.add(Word(word=token))
        posting_repo.add(
            Posting(
                word=word_in_db,
                doc=doc1_in_db,
                count=1,
                tf=1 / len(tokens),
            )
        )

    results = search(session, ["tdd"])
    assert len(results) == 1
    assert results[0].id == doc1_in_db.id


def test_search_different_tf_values(session, doc_repo, posting_repo, word_repo):
    doc1_in_db = doc_repo.add(Doc(uri="test1"))
    doc2_in_db = doc_repo.add(Doc(uri="test2"))
    token = "tdd"

    word_in_db = word_repo.add(Word(word=token))
    posting_repo.add(
        Posting(
            word=word_in_db,
            doc=doc1_in_db,
            count=3,
            tf=3 / 5,
        )
    )
    posting_repo.add(
        Posting(
            word=word_in_db,
            doc=doc2_in_db,
            count=1,
            tf=1 / 5,
        )
    )

    results = search(session, [token])
    assert len(results) == 2
    assert results[0].id == doc1_in_db.id
    assert results[1].id == doc2_in_db.id
