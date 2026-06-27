from app.core.schemas import Decision, EngineResult

UNKNOWN = "document_inconnu"


def _known(result: EngineResult | None) -> bool:
    return bool(result and result.top_type and result.top_type != UNKNOWN and result.score > 0)


def decide(
    *,
    ocr_confidence: float,
    is_blank: bool,
    bm25: EngineResult,
    graphic: EngineResult | None = None,
    barcode_coherent: bool | None = None,
) -> Decision:
    reasons: list[str] = []
    graphic = graphic or EngineResult(top_type=UNKNOWN, score=0.0)

    if is_blank:
        return Decision(
            status="rejected",
            proposed_type=UNKNOWN,
            risk_level="high",
            requires_human_review=False,
            reasons=["Page blanche détectée."],
        )

    if ocr_confidence < 0.20:
        return Decision(
            status="rejected",
            proposed_type=UNKNOWN,
            risk_level="high",
            requires_human_review=False,
            reasons=["OCR quasi nul ou inexploitable."],
        )

    if barcode_coherent is False:
        return Decision(
            status="human_review",
            proposed_type=bm25.top_type or graphic.top_type or UNKNOWN,
            risk_level="high",
            requires_human_review=True,
            reasons=["Code-barres contradictoire avec les résultats IA."],
        )

    bm25_known = _known(bm25)
    graphic_known = _known(graphic)
    same_type = bm25_known and graphic_known and bm25.top_type == graphic.top_type
    bm25_margin_ok = bm25.margin is not None and bm25.margin >= 2.0
    bm25_score_ok = bm25.score >= 5.0
    ocr_ok = ocr_confidence >= 0.80

    if bm25_known and bm25_score_ok and bm25_margin_ok and ocr_ok and (same_type or not graphic_known):
        if same_type:
            reasons.append("Les moteurs graphique et textuel convergent.")
        else:
            reasons.append("Le moteur BM25 est suffisamment discriminant pour ce POC.")
        reasons.extend([
            "La qualité OCR est suffisante.",
            "La marge de décision BM25 est acceptable.",
        ])
        return Decision(
            status="automatic",
            proposed_type=bm25.top_type or UNKNOWN,
            risk_level="low",
            requires_human_review=False,
            reasons=reasons,
        )

    if bm25_known:
        reasons.append("Le moteur BM25 propose un type mais les signaux ne suffisent pas pour automatiser.")
    else:
        reasons.append("Aucun type documentaire suffisamment discriminant.")
    if graphic_known and not same_type:
        reasons.append("Les moteurs ne convergent pas clairement.")
    if not bm25_margin_ok:
        reasons.append("La marge BM25 est insuffisante ou absente.")
    if not bm25_score_ok:
        reasons.append("Le score BM25 est inférieur au seuil automatique.")
    if not ocr_ok:
        reasons.append("La confiance OCR est inférieure au seuil automatique.")

    return Decision(
        status="human_review",
        proposed_type=bm25.top_type or graphic.top_type or UNKNOWN,
        risk_level="medium",
        requires_human_review=True,
        reasons=reasons,
    )
