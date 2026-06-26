from app.services.bm25_classifier_service import BM25Classifier, tokenize


def test_tokenize_handles_french_accents():
    assert tokenize("Facture de crèche - période d'accueil") == [
        "facture",
        "de",
        "crèche",
        "période",
        "d'accueil",
    ]


def test_bm25_classifier_returns_expected_type(tmp_path):
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    (examples_dir / "facture_creche.txt").write_text(
        "crèche enfant garde facture période montant accueil", encoding="utf-8"
    )
    (examples_dir / "rib.txt").write_text(
        "iban bic titulaire compte banque relevé identité bancaire", encoding="utf-8"
    )

    classifier = BM25Classifier(examples_dir)
    result = classifier.classify("Voici une facture de crèche pour une période de garde enfant.")

    assert result.top_type == "facture_creche"
    assert result.score > 0
    assert result.second_type == "rib"
    assert result.margin is not None


def test_bm25_classifier_handles_empty_text(tmp_path):
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    (examples_dir / "rib.txt").write_text("iban bic banque", encoding="utf-8")

    classifier = BM25Classifier(examples_dir)
    result = classifier.classify("")

    assert result.top_type == "document_inconnu"
    assert result.score == 0.0
