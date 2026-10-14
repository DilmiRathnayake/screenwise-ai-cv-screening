# SCREENWISE — Model 2: IT Candidate Ranking Dataset

**Scope:** Information Technology industry only. No other industry is represented — this
was a deliberate scope cut agreed with the supervisor to avoid the accuracy loss caused by
mixing heterogeneous, low-comparability industries into a single ranking model.

Generated with: `python generate_model2_it_dataset.py --samples 10000 --seed 42`

---

## A. Dataset Schema

**`ranking_dataset.csv`** (10,000 rows, one row = one job–candidate pair)

| Group | Columns |
|---|---|
| Job | `job_id, job_title, seniority_level, job_description, required_skills, preferred_skills, minimum_experience_years, preferred_experience_years, required_education, preferred_education, required_certifications, preferred_certifications, required_project_types, technical_requirements, responsibilities, soft_skill_requirements` |
| Candidate | `candidate_id, candidate_skills, candidate_education, candidate_experience_years, candidate_job_titles, candidate_projects, candidate_certifications, candidate_profile_text, candidate_experience_description, candidate_project_description` |
| Match components (features, NOT leakage — see §K) | `required_skill_match, preferred_skill_match, experience_match, project_relevance, education_match, certification_match, semantic_similarity` |
| Targets | `relevance_score (0–100), relevance_label (0–4), rank_within_job` |
| Metadata (diagnostic only, drop before training) | `match_tier, candidate_archetype` |

Multi-value fields are `;`-joined strings; an empty/optional field is written as the literal
`NONE` (never a blank string) so it is never mistaken for a missing value.

**`pairwise_ranking_dataset.csv`**: `job_id, candidate_a_id, candidate_b_id, candidate_a_score, candidate_b_score, preferred_candidate` — up to 5 pairs sampled per job, for learning-to-rank (LambdaMART-style) experiments.

---

## B. IT Job Roles (45)

Software Engineer, Software Developer, Full Stack Developer, Frontend Developer, Backend
Developer, React Developer, Next.js Developer, Node.js Developer, Java Developer, Python
Developer, C# Developer, .NET Developer, PHP Developer, Laravel Developer, Mobile
Application Developer, Android Developer, Flutter Developer, React Native Developer, DevOps
Engineer, Cloud Engineer, Cloud/DevOps Engineer, Data Analyst, Data Scientist, Machine
Learning Engineer, AI Engineer, NLP Engineer, QA Engineer, Software QA Engineer, Automation
Tester, Manual Tester, Cybersecurity Analyst, Cybersecurity Engineer, Network Engineer,
System Administrator, Database Administrator, Data Engineer, UI/UX Designer, Product
Designer, Technical Support Engineer, IT Support Engineer, Solutions Engineer, Software
Architect (see `taxonomy.py::ROLES` for the exact list and category mapping).

## C. Skill Taxonomy

12 controlled categories (`programming, frontend, backend, database, cloud, devops, testing,
data, ai_ml, mobile, ui_ux, swe, security`), ~110 unique skills total, plus a hand-curated
**skill relationship graph** (`SKILL_RELATIONS`, e.g. React↔JavaScript/TypeScript/Next.js,
Django↔Python, Docker↔Kubernetes). The relationship graph feeds only the `semantic_similarity`
component — it never inflates `required_skill_match`, so a candidate cannot look like a
required-skill match just because they know a *related* technology.

## D. Candidate-Generation Methodology

Each job is assigned 6–20 candidates (mean ≈15), drawn from a **match-tier distribution**
(`very_high 15% / high 25% / moderate 30% / low 20% / very_low 10%`, sampled per-job so the
realized mix varies job to job rather than being forced). Each tier maps to a required/
preferred skill-coverage range (e.g. `very_high` → 90–100% of required skills present;
`very_low` → 0–15%). Within tiers, one of nine **archetypes** is sampled:

`strong_match, overqualified, underqualified, partial_skill, career_switch,
strong_project_low_experience, experienced_missing_skills, education_no_experience,
wrong_specialization`

Archetypes independently perturb experience, education, and project history so that skill
overlap, experience, and education are **not collinear** — e.g. `overqualified` candidates
have high skill coverage *and* far more experience than required; `strong_project_low_experience`
candidates have good skill/project coverage but low tenure. Realized counts (this run):
strong_match 2,792 · overqualified 1,255 · underqualified 1,187 · strong_project_low_experience
997 · partial_skill 996 · career_switch 991 · experienced_missing_skills 662 ·
education_no_experience 649 · wrong_specialization 471.

## E. Job-Generation Methodology

Role → seniority (weighted random across Intern…Lead, each with a realistic experience
band) → required/preferred skills sampled from that role's primary/secondary taxonomy
categories (4–7 required, 2–5 preferred) → education, certification (role-dependent: cloud/
devops/security/database roles are more likely to require a cert), and project-type
requirements drawn from the same categories. `job_description` is assembled from randomized
natural-language templates + the job's own requirements, never a keyword join.

## F. Reference Relevance-Score Methodology

Score = `100 × Σ(component × weight)`, computed **after** all job/candidate attributes exist,
from independent evidence only:

| Component | Weight | Basis |
|---|---|---|
| Required skill match | 0.35 | `\|required ∩ candidate\| / \|required\|` |
| Preferred skill match | 0.15 | same, over preferred set |
| Experience match | 0.15 | piecewise: penalized below minimum, rewarded up to preferred, mildly penalized far past preferred (over-qualification) |
| Project relevance | 0.15 | overlap between candidate's project types and the job's required project types |
| Education match | 0.10 | candidate education rank vs. required rank |
| Certification match | 0.05 | required/preferred certification overlap |
| Semantic similarity | 0.05 | job's required∪preferred skills vs. candidate skills **expanded through the skill-relationship graph** — a supporting signal only |

Role differentiation (e.g. React/TypeScript mattering for Frontend but not DevOps) is
achieved structurally: each role's `required_skills`/`preferred_skills` are drawn only from
that role's relevant taxonomy categories, so the same weighted formula naturally rewards
role-appropriate skills without a separate per-role weight table. This is a documented
simplification; a per-role weight table is a natural extension (see §O).

## G. Label-Generation Methodology

`relevance_label` from fixed, documented score thresholds (not tuned to hit a target
accuracy):

| Score range | Label | Meaning |
|---|---|---|
| 0–20 | 0 | Not Relevant |
| 20–40 | 1 | Low Relevance |
| 40–60 | 2 | Moderate Relevance |
| 60–80 | 3 | High Relevance |
| 80–100 | 4 | Very High Relevance |

Realized distribution (this run): 0→259, 1→2,423, 2→2,999, 3→3,452, 4→867. The scarcity of
label 0 is intentional — a genuinely "not relevant" IT-to-IT pairing is uncommon even for hard
negatives (§H), which typically land in Low/Moderate.

## H. Hard-Negative Methodology

The `wrong_specialization` archetype builds a candidate's skill set from an **unrelated
role's primary category pool** (e.g., a DevOps job paired with a candidate whose skills are
React/Figma/CSS), with only 0–15% accidental overlap with the job's actual requirements. This
produces IT-plausible but role-mismatched negatives, rather than only trivially unrelated
ones, which is what makes the ranking task non-trivial.

## I. Train / Validation / Test Methodology

70/15/15 split by **`job_id` groups** (`group_aware_split`), not a naive random row split:
every candidate for a given job stays entirely inside one split. Because `candidate_id` is
job-scoped (`C{job_id}_{n}` — candidates are generated per job, not reused across jobs), this
also makes job-candidate-pair leakage structurally impossible. Realized split (seed=42):

| Split | Jobs | Pairs |
|---|---|---|
| train | 466 | 7,184 |
| validation | 99 | 1,400 |
| test | 101 | 1,416 |

## J. Leakage-Prevention Methodology

`validate_model2_dataset.py::check_split_leakage` computes, for every split pair, the size of
the `job_id` set intersection and the `(job_id, candidate_id)` pair-set intersection; both are
asserted to be zero at generation time and re-verified independently at validation time.
`check_near_duplicate_text` buckets `candidate_profile_text` by a normalized-prefix hash as a
fast first-pass near-duplicate flag (this run: 561 buckets covering 1,881 of 10,000 rows —
expected given a template-based generator; a stronger embedding-based near-duplicate pass
belongs in `prepare_model2_features.py`).

## K. Feature-Engineering / Anti-Leakage Note

The seven match components (`required_skill_match` … `semantic_similarity`) are **model
inputs**, not the target — they are the same evidence a recruiter would look at, computed
independently of `relevance_score`. `relevance_score` is a fixed linear combination of them
for dataset-construction purposes only; a real ranking model should learn its own combination
(and ideally from the *raw* skill sets/text rather than the pre-aggregated components) so it
isn't just re-deriving the known formula. Do not feed `relevance_score`, `relevance_label`, or
`rank_within_job` back in as a feature — only `match_tier`/`candidate_archetype` and the score/
label/rank columns are excluded from the feature set in `prepare_model2_features.py`.

## L–M. Ranking-Model & Evaluation Methodology

Pipeline scripts (run from `model2_it/`):

```bash
python prepare_model2_features.py --datadir datasets/model2_it
python train_model2.py --features-dir features
python evaluate_model2.py --features-dir features --model-dir models/best_model
```

- **Features:** raw-field engineering + cached `all-MiniLM-L6-v2` embeddings → `features/*_features.csv`
- **Model:** LightGBM LambdaMART grouped by `job_id`; hyperparameters tuned on validation only
- **Baseline:** required-skill overlap (no ML)
- **Metrics:** `evaluation/model2_metrics.json` + `evaluation/model2_evaluation_report.md` (test split only)

Optional real resume text (Kaggle Resume Dataset, IT category):

```bash
python generate_model2_it_dataset.py --samples 10000 --seed 42 \
  --real_candidates "path/to/Resume.csv" --real_text_fraction 0.12
```

Rows tagged with `data_source` (`synthetic` | `real_kaggle`).

## N. Computational Requirements

Pure Python + NumPy/pandas, no GPU. Generation of 10,000 rows completes in ~2 seconds on a
standard laptop; output is under 15 MB total across all CSVs.

## O. Limitations

- **Synthetic data**: scores are generated from a fixed, documented formula, not observed
  recruiter decisions. This lets us control leakage and label bias precisely, but means the
  dataset can only validate whether a model can recover *this* scoring logic — not whether
  that logic matches real recruiter judgment. Real-world validation (e.g. against actual
  hiring outcomes) is still necessary before any production use.
- **Per-role weighting is uniform**: the same 7-component weight table is used for every
  role; only *which skills* count as required/preferred varies by role. A true DevOps-vs-
  Frontend weight table (per §10 of the original spec) is a documented but unimplemented
  refinement.
- **Text realism**: job/candidate text is template-generated. It is diverse enough to avoid
  near-duplicate collapse in most rows but is not indistinguishable from real job postings/
  resumes. Real Kaggle postings (LinkedIn Software Engineering Jobs, 1.3M LinkedIn Jobs &
  Skills, Resume Dataset) can be pooled in as an additional phrasing source without changing
  the schema — see the optional `--real_jobs/--real_candidates` hooks.
- **Label-generation bias**: because thresholds and weights are fixed by the dataset author
  (not learned from real hiring data), the "ground truth" itself may not reflect real-world
  recruiter priorities, and any reported model accuracy should be read as "agreement with this
  synthetic rubric," not "real-world hiring accuracy."
