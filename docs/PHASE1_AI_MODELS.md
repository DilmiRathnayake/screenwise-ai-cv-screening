# AI Service — API & Training Guide (Phase 1)

## Extraction pipeline

1. Upload CV (PDF / DOCX / PNG / JPEG)
2. Format router selects PyMuPDF, python-docx, or Tesseract
3. Text cleaning + section parser + spaCy NER
4. Communication quality proxy score
5. Structured `CandidateProfile` JSON

## Ranking pipeline

1. Resolve industry weight template (or job overrides)
2. Section-aware Sentence-Transformer similarities (skills / experience / education / projects / full)
3. Six criterion scores (skills, experience, projects, education, communication, certifications)
4. Weighted sum fused with semantic similarity → match % + explanation

## IT dataset training (current)

```bash
cd ai-service
python -m training.preprocess_it_datasets
python -m training.train_ner --epochs 30 --weak-rows 0 --seed 42
python -m training.train_ranker --eval-split test
pytest -q
```

Full accuracy report: **[IT_DATASET_AND_MODELS.md](./IT_DATASET_AND_MODELS.md)**

| Model | Test F1 | Key metric |
|-------|---------|------------|
| Model 01 (NER) | 0.9877 | Per-entity F1 in `models/extraction/metrics.json` |
| Model 02 (Ranking) | 0.4057* | Spearman 0.8255 in `models/ranking/metrics.json` |

\*Binary F1 on imbalanced IT shortlist labels; see IT doc for NDCG/MRR pair metrics.
