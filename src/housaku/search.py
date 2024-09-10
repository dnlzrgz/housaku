from math import log
from sqlalchemy import func, select
from sqlalchemy.orm.session import Session
from housaku.models import Doc, Posting, Word


def search(session: Session, tokens: list[str], limit: int | None = None) -> list[Doc]:
    num_docs = session.scalar(select(func.count()).select_from(Doc))
    if not num_docs:
        return []

    postings = session.scalars(
        select(Posting).join(Word).where(Word.word.in_(tokens))
    ).all()

    df_counts = session.execute(
        select(Word.word, func.count(Posting.doc_id))
        .join(Posting)
        .where(Word.word.in_(tokens))
        .group_by(Word.word)
    ).fetchall()

    idf_values = {word: log(num_docs / (df if df > 0 else 1)) for word, df in df_counts}

    tf_idf_scores = {}
    for posting in postings:
        word = posting.word.word
        tf_idf = posting.tf * idf_values.get(word, 0)
        tf_idf_scores[posting.doc_id] = tf_idf_scores.get(posting.doc_id, 0) + tf_idf

    sorted_doc_ids = sorted(
        tf_idf_scores.keys(),
        key=lambda doc_id: tf_idf_scores[doc_id],
        reverse=True,
    )

    stmt = select(Doc).where(Doc.id.in_(sorted_doc_ids))
    if limit:
        stmt = stmt.limit(limit)

    documents = session.scalars(stmt).all()

    return list(documents)
