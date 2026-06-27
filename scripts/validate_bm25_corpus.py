#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SNAKE_CASE = re.compile(r"^[a-z0-9_]+\.txt$")
EMAIL = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
IBAN = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")
PHONE = re.compile(r"(?:(?:\+33|0)\s*[1-9](?:[\s.-]*\d{2}){4})")
LONG_NUMBER = re.compile(r"\b\d{10,}\b")


def inspect_file(path: Path, min_words: int) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    if not SNAKE_CASE.match(path.name):
        errors.append("Le nom du fichier doit être en snake_case et finir par .txt.")

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return {"file": path.name, "ok": False, "word_count": 0, "char_count": 0, "errors": ["Le fichier n'est pas encodé en UTF-8."], "warnings": warnings}

    words = re.findall(r"[\wÀ-ÿ']+", text, flags=re.UNICODE)
    if not text.strip():
        errors.append("Le fichier est vide.")
    if len(words) < min_words:
        warnings.append(f"Corpus court : {len(words)} mots, seuil recommandé {min_words}.")
    if EMAIL.search(text):
        warnings.append("Email potentiel détecté : vérifier l'anonymisation.")
    if IBAN.search(text):
        warnings.append("IBAN potentiel détecté : vérifier l'anonymisation.")
    if PHONE.search(text):
        warnings.append("Téléphone potentiel détecté : vérifier l'anonymisation.")
    if LONG_NUMBER.search(text):
        warnings.append("Numéro long potentiel détecté : vérifier l'anonymisation.")

    unique_words = {word.lower() for word in words}
    if len(unique_words) < 25:
        warnings.append("Vocabulaire peu varié : le typage BM25 risque d'être faible.")

    return {"file": path.name, "ok": not errors, "word_count": len(words), "char_count": len(text), "unique_word_count": len(unique_words), "errors": errors, "warnings": warnings}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate BM25 corpus files for the POC.")
    parser.add_argument("directory", nargs="?", default="data/bm25_examples")
    parser.add_argument("--min-words", type=int, default=80)
    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.exists():
        print(json.dumps({"ok": False, "error": f"Directory not found: {directory}"}, ensure_ascii=False, indent=2))
        return 1

    files = sorted(directory.glob("*.txt"))
    if not files:
        print(json.dumps({"ok": False, "error": "No .txt corpus files found."}, ensure_ascii=False, indent=2))
        return 1

    results = [inspect_file(path, args.min_words) for path in files]
    payload = {"ok": all(item["ok"] for item in results), "directory": str(directory), "file_count": len(files), "files": results}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
