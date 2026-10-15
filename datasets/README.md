# Datasets

Full findings and numbers: [`docs/DATASET_AUDIT.md`](../docs/DATASET_AUDIT.md). The original files in this folder are never modified.

## Annotated resume dataset (this folder)

| Folder | Content | Files |
|---|---|---|
| `ResumesJsonAnnotated/ResumesJsonAnnotated/` | `{"text": ..., "annotations": [[start, end, "SKILL: word"], ...]}` | 5,029 JSON |
| `ResumesPDF/ResumesPDF/` | the same CVs as PDF | 5,035 PDF |

- **Type:** real-looking, public CVs with automatic-looking `SKILL` annotations. Not synthetic. Contains personal data (emails, phone numbers): do not print or publish its content.
- **Source:** not verifiable from the repository. Suggested by the author as `https://www.kaggle.com/datasets/haidermaseeh/resume-dataset`. **Licence unknown**: check the Kaggle page.
- **No categories, no relevance labels, no Excel file** (an Excel file was expected but is not in the repository).
- **Valid use:** robustness testing of the extraction pipeline. **Not valid:** NER training or evaluation (noisy, overlapping labels), classification, ranking evaluation.

## Derived files (`processed/`)

Created by `python datasets/prepare_resume_dataset.py` (run from the project root, standard library plus the project's `model2_it/taxonomy.py`):

| File | Content |
|---|---|
| `processed/resume_json_index.csv` | one row per JSON record: ids, text length, span counts, duplicate pointer, IT-skill hits, `it_candidate` flag. No resume text. |
| `processed/resume_dataset_summary.json` | aggregate counts |
| `processed/resume_compat_check.json` | output of `ai-service/evaluation/resume_dataset_compat_check.py` (aggregate robustness numbers) |

Preparation rules: nothing is deleted or rewritten. Empty texts and duplicates are flagged, not removed. `it_candidate = 1` means at least 5 distinct skills from `model2_it/taxonomy.py`
(a heuristic, not a category label; change with `--min-it-skills`).

Compatibility check (from `ai-service/`): `python -m evaluation.resume_dataset_compat_check --sample 100`.

## Other datasets in the project (different sources)

| Location | Content | Type |
|---|---|---|
| `ai-service/datasets/processed/ner/` | `it_ner_{train,val,test,full}.json`, 1,000 CVs with NAME/EMAIL/SKILL/DEGREE/CERTIFICATION entities | synthetic, annotated (generated for this project) |
| `ai-service/datasets/processed/ranking/` | 1,497 candidates, 200 jobs, 2,000 candidate-job pairs | synthetic |
| `model2_it/datasets/model2_it/` | 10,000 job-candidate pairs for the LambdaMART research model | synthetic |

The legacy Kaggle files named in the report (for example `resume_data.csv`, `AI_Resume_Screening.csv`, `Entity Recognition in Resumes.json`) are **not** in the repository.
