# Dataset audit — annotated resume dataset (JSON + PDF)

Audited on 2026-10-15 from the files committed in `ff0f667` ("new datasets"). Every number below was computed from the files by
[`datasets/prepare_resume_dataset.py`](../datasets/prepare_resume_dataset.py) and
[`ai-service/evaluation/resume_dataset_compat_check.py`](../ai-service/evaluation/resume_dataset_compat_check.py) (outputs in `datasets/processed/`).
The original files were not modified. No model was trained or changed.

## 1. What is actually in the repository

| Item | Finding |
|---|---|
| `datasets/ResumesJsonAnnotated/ResumesJsonAnnotated/` | 5,029 JSON files, 42.2 MB, named `cv (N)_annotated.json` |
| `datasets/ResumesPDF/ResumesPDF/` | 5,035 PDF files, about 630 MB, named `cv (N).pdf` |
| **Excel spreadsheet** | **Not found.** No `.xlsx`/`.xls` exists in the repository, in Git history, or in the Downloads, Desktop, Documents or WhatsApp folders on this device. The spreadsheet was probably not committed. Nothing in this audit covers it. |
| README / metadata / licence | **None** in the dataset folders. Git history has a single commit with the message "new datasets". |

## 2. Source and licence

- **Source: not verifiable from the repository.** You supplied `https://www.kaggle.com/datasets/haidermaseeh/resume-dataset`. The folder names are consistent with a resume
  dataset published as PDFs plus annotated JSON, but no file in the repository confirms the Kaggle page, the title or the author.
- **Licence: unknown.** Check the licence on the Kaggle page before redistributing or quoting the data.
- Whether the Excel file comes from the same page cannot be determined, because the file is absent.

## 3. Relationship between the two folders

The JSON and PDF folders are two formats of the same collection: 5,029 JSON files match 5,029 PDFs one-to-one by number (`cv (N)`).
Six PDFs have no JSON (numbers 1054, 1055, 2586, 3138, 3498, 4022). The folders are not two different datasets.

This collection is **not** the same as the project's existing IT datasets (`ai-service/datasets/processed/`, `model2_it/datasets/`), which are synthetic and have a different schema.

## 4. JSON structure and quality

Each file is a JSON object with exactly two keys: `text` (string, the resume text) and `annotations` (list of `[start, end, label]`).

| Check | Result |
|---|---|
| Files that parse as valid JSON (UTF-8) | 5,029 of 5,029 |
| Empty `text` | 47 |
| Records with zero annotations | 58 |
| Duplicate texts (identical after trim and lower-casing; 1st copy not counted) | 1,651 (excluding empty texts) |
| Text length (characters), min / median / max | 0 / 3,588 / 99,973 |
| Files containing a lone surrogate character (encoding fault) | 1 |
| Annotation spans in total | 538,482 |
| Spans with invalid offsets (outside the text) | 0 |
| Overlapping span pairs | 78,983, spread over 4,671 records |
| Distinct label types | 1 (`SKILL`) |
| Label format | `SKILL: <word>`, where the word equals the annotated text in all 538,482 spans |
| Distinct annotated words | 12,695 |

**Quality concern.** The most frequent "skills" are generic words, not skills: `com` (3,874), `skills` (3,805), `work` (3,679), `personal` (3,458), `knowledge` (3,417),
`english` (3,399), `gmail` (3,238), `nationality` (2,588), `marital status` (2,266). The labels look like automatic keyword tagging rather than a human-checked skill annotation.
Real IT skills appear but are rare in the annotations (for example `python` 239, `java` 232, `docker` 14, `react` 10).

## 5. Categories and relevance labels

- **No category field exists** in the JSON (only `text` and `annotations`). An "IT category" therefore cannot be taken from the data.
- **No candidate-job relevance labels exist.** The dataset cannot be used to evaluate ranking.
- **Personal data.** 3,713 of 5,029 texts contain an email-like string and 4,202 contain a phone-like string. These appear to be real people's CVs. Do not print, publish or demo
  their content, and confirm that you are allowed to host them in a public repository.

## 6. IT subset (heuristic, not ground truth)

Because there is no category, `prepare_resume_dataset.py` flags `it_candidate = 1` when the text contains at least **5 distinct skills** from the project's own IT taxonomy
(`model2_it/taxonomy.py`, skills of 3+ characters, whole-word, case-insensitive). The rule is explicit and can be changed with `--min-it-skills`.

| | Records |
|---|---|
| All records | 5,029 |
| Flagged IT (at least 5 IT-taxonomy skills) | 370 |
| Flagged IT, unique texts | 279 |

Only about 7% of the dataset passes the rule, so the collection is mostly not IT. The flag is a convenience for sampling, and some flagged records may not be IT roles.
The derived file is `datasets/processed/resume_json_index.csv` (one row per JSON record: ids, lengths, counts, duplicate pointer, IT hits). It contains **no resume text**.

## 7. PDFs

- 5,035 files, none zero-byte. 1,222 are byte-identical duplicates of another PDF.
- In a sample of 100 IT-flagged PDFs, all 100 produced readable text through the project's existing `OCRService` (PyMuPDF; 98 `pymupdf`, 2 `hybrid`). Tesseract is not installed on the
  test machine, so image OCR was not exercised.

## 8. Compatibility check with the existing extraction pipeline (software test, not ML evaluation)

Sample: 100 unique IT-flagged records (seed 42), existing `ExtractionService`, **rule-only** (the trained spaCy NER model is not in this checkout).

| Result | Value |
|---|---|
| Records that made the pipeline crash | 0 of 100 |
| Records with no technical skills found | 0 of 100 (median 28 skills per CV) |
| Records with no education found | 77 of 100 |
| Records with no experience found | 62 of 100 |
| Median time per record | about 2 ms |

Reading: the pipeline runs on this dataset without errors, but the rule-based section parser misses the education and experience sections on most of these less-structured CVs.
This is consistent with the limitation stated in your report (Section 7.4: real, unstructured CVs score lower than the synthetic IT dataset). There is no ground truth for these fields,
so no accuracy is claimed.

## 9. Valid and invalid uses

| Use | Verdict |
|---|---|
| Robustness / smoke testing of PDF reading and extraction | **Valid** (Section 8) |
| Illustrating the difference between synthetic and real CVs in the viva | **Valid** (Section 8; use aggregate numbers only) |
| Training or fine-tuning spaCy NER | **Not valid as is.** One generic label type, noisy words, 78,983 overlapping spans (spaCy rejects overlapping entities). Needs cleaning first. Not done. |
| Evaluating NER / skill extraction | **Not valid.** The annotations are not a reliable ground truth. |
| Resume classification | **Not possible.** No category labels. |
| Candidate-job matching or ranking evaluation | **Not possible.** No relevance labels. |

## 10. Limitations

- Source, licence and the Excel file are unverified (Sections 1 and 2).
- Real personal data is present (Section 5).
- About a third of the texts are duplicates (1,651 of 4,982 non-empty texts), so any statistics should use the `duplicate_of_cv_number` column to de-duplicate.
- The IT flag is a heuristic.
