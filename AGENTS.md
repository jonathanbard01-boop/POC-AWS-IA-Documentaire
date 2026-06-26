# AGENTS.md

## Projet
POC AWS IA documentaire : OCR, OpenCV, BM25, moteur de décision, front-office et back-office.

## Règles
- Préserver une architecture modulaire.
- Ne pas ajouter de secret dans le repo.
- Tout traitement IA doit produire des scores et motifs explicables.
- Les documents douteux doivent être orientés vers contrôle humain.
- Ne pas introduire de modèle GPU dans le Palier 1.

## Priorité de réalisation
1. API d'ingestion.
2. Worker OCR/OpenCV.
3. BM25.
4. Moteur de décision.
5. Front-office.
6. Back-office.
