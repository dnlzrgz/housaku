import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from housaku.repositories import DocRepository
from housaku.models import Base, Doc


@pytest.fixture(scope="function")
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture
def docs_repository(session):
    return DocRepository(session)


@pytest.fixture
def new_doc():
    return Doc(uri="./guide.txt", content="Don't Panic.", properties={})


def test_add_document(docs_repository, new_doc):
    doc_in_db = docs_repository.add(new_doc)

    assert doc_in_db is not None
    assert doc_in_db.id == 1
    assert doc_in_db.content == new_doc.content


def test_get_document_by_id(docs_repository, new_doc):
    docs_repository.add(new_doc)

    doc_in_db = docs_repository.get(id=1)
    assert doc_in_db is not None
    assert doc_in_db.id == 1
    assert doc_in_db.content == new_doc.content


def test_get_document_by_attributes(docs_repository, new_doc):
    docs_repository.add(new_doc)

    doc_in_db = docs_repository.get_by_attributes(uri=new_doc.uri)
    assert doc_in_db is not None
    assert doc_in_db.id == 1
    assert doc_in_db.content == new_doc.content


def test_get_all_documents(docs_repository):
    for i in range(5):
        docs_repository.add(Doc(uri=f"{i}.txt", content="w" * i, properties={}))

    docs_in_db = docs_repository.get_all()
    assert len(docs_in_db) == 5


def test_update_document(docs_repository, new_doc):
    doc_in_db = docs_repository.add(new_doc)
    assert doc_in_db is not None
    assert doc_in_db.content == new_doc.content
    old_content = doc_in_db.content

    docs_repository.update(doc_in_db.id, content="Maybe panic a little.")
    updated_doc = docs_repository.get(doc_in_db.id)
    assert updated_doc is not None
    assert updated_doc.content != old_content


def test_delete_document(docs_repository, new_doc):
    doc_in_db = docs_repository.add(new_doc)
    assert doc_in_db is not None

    deleted_doc = docs_repository.delete(doc_in_db.id)
    assert deleted_doc is not None

    doc_in_db = docs_repository.get(id=doc_in_db.id)
    assert doc_in_db is None
