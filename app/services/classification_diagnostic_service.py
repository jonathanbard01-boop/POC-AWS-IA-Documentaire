from __future__ import annotations

from app.core.decision_engine import UNKNOWN
from app.core.schemas import ClassificationTestResponse, Decision, EngineResult
from app.services.runtime_corpus_service import classify_runtime_text, list_runtime_corpus


def get_corpus_summary():
    return list_runtime_corpus()


def classify_text_for_diagnostic(text: str) -> ClassificationTestResponse:
    bm25 = classify_runtime_text(text)
    decision = _decide_bm25_only(text=text, bm25=bm25)
    return ClassificationTestResponse(text_length=len(text), bm25_result=bm25, decision=decision)


def _decide_bm25_only(*, text: str, bm25: EngineResult) -> Decision:
    if not text.strip():
        return Decision(
            status="rejected",
            proposed_type=UNKNOWN,
            risk_level="high",
            requires_human_review=False,
            reasons=["Texte vide : aucun typage possible."],
        )

    if not bm25.top_type or bm25.top_type == UNKNOWN or bm25.score <= 0:
        return Decision(
            status="human_review",
            proposed_type=UNKNOWN,
            risk_level="medium",
            requires_human_review=True,
            reasons=["Aucun signal BM25 suffisamment discriminant."],
        )

    margin_ok = bm25.margin is not None and bm25.margin >= 2.0
    score_ok = bm25.score >= 5.0

    if score_ok and margin_ok:
        return Decision(
            status="automatic_candidate",
            proposed_type=bm25.top_type,
            risk_level="low",
            requires_human_review=False,
            reasons=["Score BM25 supérieur au seuil diagnostic.", "Marge suffisante avec le second type."],
        )

    reasons = ["Le moteur BM25 propose un type, mais le score ou la marge restent insuffisants."]
    if not score_ok:
        reasons.append("Score BM25 inférieur au seuil diagnostic de 5.0.")
    if not margin_ok:
        reasons.append("Marge BM25 inférieure au seuil diagnostic de 2.0.")

    return Decision(
        status="human_review",
        proposed_type=bm25.top_type,
        risk_level="medium",
        requires_human_review=True,
        reasons=reasons,
    )
