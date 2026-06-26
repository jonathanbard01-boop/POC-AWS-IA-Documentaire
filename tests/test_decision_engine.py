from app.core.decision_engine import decide
from app.core.schemas import EngineResult


def test_blank_page_is_rejected():
    decision = decide(
        ocr_confidence=0.9,
        is_blank=True,
        bm25=EngineResult(top_type="facture_creche", score=10, margin=3),
    )
    assert decision.status == "rejected"


def test_convergent_engines_are_automatic():
    decision = decide(
        ocr_confidence=0.9,
        is_blank=False,
        bm25=EngineResult(top_type="facture_creche", score=10, margin=3),
        graphic=EngineResult(top_type="facture_creche", score=0.92),
    )
    assert decision.status == "automatic"


def test_weak_margin_requires_review():
    decision = decide(
        ocr_confidence=0.9,
        is_blank=False,
        bm25=EngineResult(top_type="facture_creche", score=10, margin=0.5),
        graphic=EngineResult(top_type="facture_creche", score=0.92),
    )
    assert decision.status == "human_review"
