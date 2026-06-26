from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from rank_bm25 import BM25Okapi

from app.core.schemas import EngineResult

TOKEN_PATTERN = re.compile(r"[\wÀ-ÿ']+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


@dataclass(frozen=True)
class BM25Document:
    document_type: str
    text: str


class BM25Classifier:
    """Simple BM25 document-type classifier.

    Each .txt file in the examples directory is treated as one document example.
    The filename stem is used as the document type.
    """

    def __init__(self, examples_dir: str | Path = "data/bm25_examples") -> None:
        self.examples_dir = Path(examples_dir)
        self.documents: list[BM25Document] = []
        self._bm25: BM25Okapi | None = None
        self.rebuild()

    def rebuild(self) -> None:
        self.documents = []
        for path in sorted(self.examples_dir.glob("*.txt")):
            text = path.read_text(encoding="utf-8").strip()
            if text:
                self.documents.append(BM25Document(document_type=path.stem, text=text))

        tokenized_corpus = [tokenize(doc.text) for doc in self.documents]
        self._bm25 = BM25Okapi(tokenized_corpus) if tokenized_corpus else None

    def classify(self, text: str) -> EngineResult:
        if not text.strip() or not self._bm25 or not self.documents:
            return EngineResult(top_type="document_inconnu", score=0.0)

        query_tokens = tokenize(text)
        if not query_tokens:
            return EngineResult(top_type="document_inconnu", score=0.0)

        scores = self._bm25.get_scores(query_tokens)
        ranked = sorted(
            zip(self.documents, scores, strict=True),
            key=lambda item: float(item[1]),
            reverse=True,
        )

        top_doc, top_score = ranked[0]
        second_doc = ranked[1][0] if len(ranked) > 1 else None
        second_score = float(ranked[1][1]) if len(ranked) > 1 else None
        margin = float(top_score) - second_score if second_score is not None else None

        return EngineResult(
            top_type=top_doc.document_type,
            score=float(top_score),
            second_type=second_doc.document_type if second_doc else None,
            second_score=second_score,
            margin=margin,
        )


_default_classifier: BM25Classifier | None = None


def get_default_bm25_classifier() -> BM25Classifier:
    global _default_classifier
    if _default_classifier is None:
        _default_classifier = BM25Classifier()
    return _default_classifier
