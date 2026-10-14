"""
generate_model2_it_dataset.py

Generates the SCREENWISE Model 2 (IT Candidate Ranking) synthetic dataset:
exactly N job-candidate pairs, restricted to the IT industry, designed for
learning-to-rank (not just binary classification).

Usage:
    python generate_model2_it_dataset.py --samples 10000 --seed 42 \
        --outdir datasets/model2_it [--real_jobs FILE] [--real_candidates FILE]

Optional real-data ingestion:
    --real_jobs / --real_candidates accept a CSV with at least a free-text
    column (job description / resume text). If provided, their titles /
    text are pooled in alongside synthetic ones to diversify phrasing.
    This is OPTIONAL: the script produces a complete, valid dataset with
    zero external files.

Reproducibility: random.Random(seed) drives every stochastic choice.
"""

import argparse
import json
import logging
import os
import random
import sys
from dataclasses import dataclass, field, asdict

import numpy as np
import pandas as pd

from taxonomy import (
    CATEGORY_SKILLS, ALL_SKILLS, SKILL_RELATIONS, related_skills,
    SENIORITY_EXPERIENCE, SENIORITY_ORDER, EDUCATION_LEVELS, EDUCATION_RANK,
    CERTIFICATIONS_BY_CATEGORY, PROJECT_TYPES_BY_CATEGORY,
    ROLES, ROLE_TITLES, role_required_skill_pool, role_preferred_skill_pool,
    role_categories,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("model2_generator")

SOFT_SKILLS = [
    "communication", "teamwork", "problem-solving", "adaptability",
    "time management", "attention to detail", "collaboration under deadlines",
    "ownership and accountability", "willingness to learn", "analytical thinking",
]

TIERS = ["very_high", "high", "moderate", "low", "very_low"]
TIER_WEIGHTS = [0.15, 0.25, 0.30, 0.20, 0.10]

ARCHETYPES_BY_TIER = {
    "very_high": ["strong_match"],
    "high": ["strong_match", "overqualified"],
    "moderate": ["partial_skill", "career_switch", "strong_project_low_experience"],
    "low": ["underqualified", "experienced_missing_skills", "education_no_experience"],
    "very_low": ["wrong_specialization", "underqualified"],
}

LABEL_THRESHOLDS = [
    (0, 20, 0, "Not Relevant"),
    (20, 40, 1, "Low Relevance"),
    (40, 60, 2, "Moderate Relevance"),
    (60, 80, 3, "High Relevance"),
    (80, 101, 4, "Very High Relevance"),
]

COMPONENT_WEIGHTS = {
    "required_skill": 0.35,
    "preferred_skill": 0.15,
    "experience": 0.15,
    "project": 0.15,
    "education": 0.10,
    "certification": 0.05,
    "semantic": 0.05,
}


# --------------------------------------------------------------------------
# Text templates (natural sentences, not keyword joins)
# --------------------------------------------------------------------------
JOB_INTRO_TEMPLATES = [
    "We are looking for a {seniority_lc} {title} to join our IT team and help "
    "build reliable, scalable software.",
    "Our engineering team is hiring a {seniority_lc} {title} to contribute to "
    "ongoing product and platform initiatives.",
    "As a {seniority_lc} {title}, you will work closely with cross-functional "
    "teams to design, build and maintain high-quality software solutions.",
    "We're expanding our technology team and are seeking a {seniority_lc} "
    "{title} who is passionate about writing clean, maintainable code.",
]

JOB_RESP_TEMPLATES = [
    "Collaborate with product managers and designers to translate requirements into technical solutions.",
    "Write clean, well-tested, and maintainable code following team standards.",
    "Participate in code reviews and provide constructive feedback to peers.",
    "Debug and resolve production issues in a timely manner.",
    "Contribute to architectural decisions and technical documentation.",
    "Work in an Agile environment, participating in sprint planning and stand-ups.",
    "Mentor junior team members and share technical knowledge.",
    "Continuously improve system performance, reliability and security.",
]

CAND_SUMMARY_TEMPLATES = [
    "{title_prefix} with hands-on experience in {skills_text}.",
    "IT professional with a background in {skills_text}, looking to contribute "
    "to challenging technical projects.",
    "Motivated developer with practical exposure to {skills_text} gained through "
    "professional and personal projects.",
    "Detail-oriented IT specialist skilled in {skills_text}, with a track record "
    "of delivering working software.",
    "{title_prefix} who has applied {skills_text} across {n_years} year(s) of "
    "hands-on IT work.",
    "Builds and maintains software using {skills_text}; comfortable working "
    "both independently and within Agile teams.",
]

CAND_EXPERIENCE_TEMPLATES = [
    "Worked as a {job_title} for {years} year(s), primarily using {skills_text}.",
    "Spent {years} year(s) in {job_title} roles, contributing to projects built with {skills_text}.",
    "{years} year(s) of professional experience as a {job_title}, focused on {skills_text}.",
]

CAND_PROJECT_TEMPLATES = [
    "Built a {project} using {skills_text}.",
    "Developed a {project}, applying {skills_text} to solve real-world requirements.",
    "Contributed to a {project} as part of a small team, working primarily with {skills_text}.",
]


def _oxford(items):
    items = list(items)
    if not items:
        return "general-purpose tools"
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


# --------------------------------------------------------------------------
# Job generation
# --------------------------------------------------------------------------
def generate_job(job_idx, rng):
    title = rng.choice(ROLE_TITLES)
    seniority = rng.choice(SENIORITY_ORDER)
    min_exp, max_exp = SENIORITY_EXPERIENCE[seniority]
    min_experience_years = min_exp
    preferred_experience_years = min(max_exp, min_exp + rng.randint(1, 2))

    req_pool = role_required_skill_pool(title)
    pref_pool = role_preferred_skill_pool(title)

    n_req = rng.randint(4, min(7, len(req_pool))) if len(req_pool) >= 4 else len(req_pool)
    n_pref = rng.randint(2, min(5, len(pref_pool))) if len(pref_pool) >= 2 else len(pref_pool)

    required_skills = sorted(rng.sample(req_pool, n_req)) if req_pool else []
    preferred_skills = sorted(rng.sample(pref_pool, n_pref)) if pref_pool else []

    cats = role_categories(title)
    primary_cat = cats[0] if cats else "swe"

    required_education = rng.choice([
        "Bachelor's Degree", "Bachelor's Degree (related field)", "Diploma",
    ]) if seniority in ("Intern", "Trainee", "Junior") else rng.choice([
        "Bachelor's Degree", "Bachelor's Degree (related field)", "Master's Degree",
    ])
    preferred_education = "Master's Degree" if seniority in ("Senior", "Lead") and rng.random() < 0.4 \
        else required_education

    cert_pool = []
    for c in cats:
        cert_pool.extend(CERTIFICATIONS_BY_CATEGORY.get(c, []))
    cert_pool = sorted(set(cert_pool))
    wants_certs = primary_cat in ("cloud", "devops", "security", "database") or rng.random() < 0.25
    required_certifications = rng.sample(cert_pool, 1) if (wants_certs and cert_pool and rng.random() < 0.3) else []
    preferred_certifications = (
        rng.sample([c for c in cert_pool if c not in required_certifications],
                   min(2, max(0, len(cert_pool) - len(required_certifications))))
        if cert_pool and rng.random() < 0.5 else []
    )

    proj_pool = []
    for c in cats:
        proj_pool.extend(PROJECT_TYPES_BY_CATEGORY.get(c, []))
    proj_pool = sorted(set(proj_pool)) or ["internal software project"]
    required_project_types = rng.sample(proj_pool, min(2, len(proj_pool)))

    responsibilities = rng.sample(JOB_RESP_TEMPLATES, k=min(4, len(JOB_RESP_TEMPLATES)))
    soft_skill_requirements = rng.sample(SOFT_SKILLS, k=4)

    intro = rng.choice(JOB_INTRO_TEMPLATES).format(seniority_lc=seniority.lower(), title=title)
    skill_sentence = (
        f"The ideal candidate is proficient in {_oxford(required_skills)}."
        if required_skills else ""
    )
    pref_sentence = (
        f" Experience with {_oxford(preferred_skills)} is a strong plus."
        if preferred_skills else ""
    )
    exp_sentence = (
        f" We expect at least {min_experience_years} year(s) of relevant experience"
        f"{', with ' + str(preferred_experience_years) + ' or more preferred' if preferred_experience_years > min_experience_years else ''}."
    )
    job_description = intro + " " + skill_sentence + pref_sentence + exp_sentence + " " + \
        " ".join(responsibilities[:2])

    technical_requirements = required_skills + preferred_skills

    return {
        "job_id": f"J{job_idx:05d}",
        "job_title": title,
        "seniority_level": seniority,
        "job_description": job_description,
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "minimum_experience_years": min_experience_years,
        "preferred_experience_years": preferred_experience_years,
        "required_education": required_education,
        "preferred_education": preferred_education,
        "required_certifications": required_certifications,
        "preferred_certifications": preferred_certifications,
        "required_project_types": required_project_types,
        "responsibilities": responsibilities,
        "technical_requirements": technical_requirements,
        "soft_skill_requirements": soft_skill_requirements,
        "_primary_category": primary_cat,
        "_categories": cats,
    }


# --------------------------------------------------------------------------
# Candidate generation (tier / archetype driven)
# --------------------------------------------------------------------------
def _sample_skills_from(pool, k, rng):
    pool = list(pool)
    k = max(0, min(k, len(pool)))
    return sorted(rng.sample(pool, k)) if k > 0 else []


def generate_candidate(job, cand_idx, tier, rng):
    archetype = rng.choice(ARCHETYPES_BY_TIER[tier])
    req = job["required_skills"]
    pref = job["preferred_skills"]
    cats = job["_categories"]

    # coverage ratios by tier (fraction of job's required / preferred skills the
    # candidate actually has)
    coverage = {
        "very_high": (0.90, 1.00, 0.60, 0.90),
        "high":      (0.70, 0.90, 0.40, 0.70),
        "moderate":  (0.40, 0.70, 0.20, 0.50),
        "low":       (0.15, 0.40, 0.05, 0.30),
        "very_low":  (0.00, 0.15, 0.00, 0.15),
    }[tier]
    req_lo, req_hi, pref_lo, pref_hi = coverage

    if archetype == "wrong_specialization" and len(ROLE_TITLES) > 1:
        # hard negative: candidate's skills come from an unrelated role's
        # primary category, not from this job's own category
        other_roles = [r for r in ROLE_TITLES if ROLES[r]["primary"] != job["_categories"][:1]]
        other_role = rng.choice(other_roles) if other_roles else rng.choice(ROLE_TITLES)
        base_pool = role_required_skill_pool(other_role)
        n_have = rng.randint(2, min(5, len(base_pool))) if base_pool else 0
        candidate_skills = set(_sample_skills_from(base_pool, n_have, rng))
        # small amount of accidental overlap with this job's requirements
        overlap_n = int(len(req) * rng.uniform(0.0, 0.15))
        candidate_skills |= set(_sample_skills_from(req, overlap_n, rng))
        job_title_history = other_role
    else:
        n_req_have = int(round(len(req) * rng.uniform(req_lo, req_hi)))
        n_pref_have = int(round(len(pref) * rng.uniform(pref_lo, pref_hi)))
        candidate_skills = set(_sample_skills_from(req, n_req_have, rng))
        candidate_skills |= set(_sample_skills_from(pref, n_pref_have, rng))
        # add 0-3 unrelated extra skills for realism (nobody has *only* the job's skills)
        extra_pool = [s for s in ALL_SKILLS if s not in candidate_skills]
        candidate_skills |= set(_sample_skills_from(extra_pool, rng.randint(0, 3), rng))
        job_title_history = job["job_title"]

    min_exp = job["minimum_experience_years"]
    pref_exp = job["preferred_experience_years"]

    if archetype == "overqualified":
        experience_years = pref_exp + rng.randint(3, 8)
    elif archetype in ("underqualified",):
        experience_years = max(0, min_exp - rng.randint(1, 3))
    elif archetype == "strong_project_low_experience":
        experience_years = max(0, min_exp - rng.randint(0, 2))
    elif archetype == "education_no_experience":
        experience_years = rng.choice([0, 0, 1])
    elif archetype == "career_switch":
        experience_years = rng.randint(1, 4)
        job_title_history = rng.choice(["Technical Support Engineer", "IT Support Engineer",
                                         "QA Engineer", "Business Analyst (IT)"])
    elif archetype == "experienced_missing_skills":
        experience_years = pref_exp + rng.randint(2, 6)
    else:
        experience_years = max(0, rng.randint(min_exp, max(min_exp, pref_exp) + 2))

    if archetype == "education_no_experience":
        education = rng.choice(["Master's Degree", "Bachelor's Degree (related field)"])
    elif tier in ("very_high", "high"):
        education = rng.choice(["Bachelor's Degree", "Bachelor's Degree (related field)", "Master's Degree"])
    elif archetype == "career_switch":
        education = rng.choice(["Bachelor's Degree (unrelated field)", "Diploma", "Associate Degree"])
    else:
        education = rng.choice(EDUCATION_LEVELS)

    proj_pool = []
    for c in cats:
        proj_pool.extend(PROJECT_TYPES_BY_CATEGORY.get(c, []))
    proj_pool = sorted(set(proj_pool)) or ["internal software project"]
    if tier in ("very_high", "high") or archetype == "strong_project_low_experience":
        n_proj = rng.randint(2, 3)
        projects = _sample_skills_from(proj_pool, n_proj, rng)
    elif tier == "moderate":
        projects = _sample_skills_from(proj_pool, rng.randint(1, 2), rng)
    else:
        off_pool = [p for cat in CATEGORY_SKILLS for p in PROJECT_TYPES_BY_CATEGORY.get(cat, [])
                    if p not in proj_pool]
        projects = _sample_skills_from(off_pool or proj_pool, rng.randint(0, 1), rng)

    cert_pool = []
    for c in cats:
        cert_pool.extend(CERTIFICATIONS_BY_CATEGORY.get(c, []))
    cert_pool = sorted(set(cert_pool))
    has_cert_prob = {"very_high": 0.5, "high": 0.35, "moderate": 0.15, "low": 0.05, "very_low": 0.02}[tier]
    certifications = _sample_skills_from(cert_pool, 1, rng) if (cert_pool and rng.random() < has_cert_prob) else []

    skills_list = sorted(candidate_skills)
    rng.shuffle(skills_list)  # vary which skills lead the summary sentence, cuts duplicate phrasing
    skills_text = _oxford(skills_list[:5]) if skills_list else "general IT tools"
    profile_text = rng.choice(CAND_SUMMARY_TEMPLATES).format(
        title_prefix=rng.choice(["Software professional", "IT graduate", "Technology enthusiast",
                                  "Experienced developer", "Early-career developer"]),
        skills_text=skills_text,
        n_years=max(experience_years, 1),
    )
    skills_list = sorted(skills_list)
    experience_description = rng.choice(CAND_EXPERIENCE_TEMPLATES).format(
        job_title=job_title_history, years=experience_years, skills_text=skills_text,
    ) if experience_years > 0 else "No prior professional experience; primarily project and coursework based."
    project_description = " ".join(
        rng.choice(CAND_PROJECT_TEMPLATES).format(project=p, skills_text=skills_text) for p in projects
    ) if projects else "No significant portfolio projects documented."

    return {
        "candidate_id": f"C{job['job_id']}_{cand_idx:03d}",
        "job_id": job["job_id"],
        "candidate_skills": skills_list,
        "candidate_education": education,
        "candidate_experience_years": experience_years,
        "candidate_job_titles": [job_title_history],
        "candidate_projects": projects,
        "candidate_certifications": certifications,
        "candidate_profile_text": profile_text,
        "candidate_experience_description": experience_description,
        "candidate_project_description": project_description,
        "_tier": tier,
        "_archetype": archetype,
    }


# --------------------------------------------------------------------------
# Reference relevance score (computed AFTER attributes exist -> no leakage)
# --------------------------------------------------------------------------
def _semantic_proxy(job, candidate):
    job_terms = set(job["required_skills"]) | set(job["preferred_skills"])
    cand_terms = set(candidate["candidate_skills"])
    expanded_cand = set(cand_terms)
    for s in cand_terms:
        expanded_cand.update(related_skills(s))
    if not job_terms:
        return 0.0
    overlap = len(job_terms & expanded_cand)
    return overlap / len(job_terms)


def score_pair(job, candidate):
    req = set(job["required_skills"])
    pref = set(job["preferred_skills"])
    have = set(candidate["candidate_skills"])

    req_match = (len(req & have) / len(req)) if req else 1.0
    pref_match = (len(pref & have) / len(pref)) if pref else 1.0

    min_exp = job["minimum_experience_years"]
    pref_exp = max(job["preferred_experience_years"], min_exp)
    ce = candidate["candidate_experience_years"]
    if ce < min_exp:
        exp_score = max(0.0, 1 - (min_exp - ce) / max(1, min_exp + 1))
    elif ce <= pref_exp:
        exp_score = 0.8 + 0.2 * ((ce - min_exp) / max(1, (pref_exp - min_exp) or 1))
    else:
        over = ce - pref_exp
        exp_score = max(0.5, 1 - 0.05 * over)  # mild penalty for large overqualification

    req_edu_rank = EDUCATION_RANK.get(job["required_education"], 3)
    cand_edu_rank = EDUCATION_RANK.get(candidate["candidate_education"], 3)
    edu_score = 1.0 if cand_edu_rank >= req_edu_rank else max(0.0, 1 - 0.25 * (req_edu_rank - cand_edu_rank))

    required_projects = set(job["required_project_types"])
    cand_projects = set(candidate["candidate_projects"])
    proj_score = (len(required_projects & cand_projects) / len(required_projects)) if required_projects else \
        (0.5 if cand_projects else 0.0)
    if not required_projects and cand_projects:
        proj_score = min(1.0, 0.3 + 0.2 * len(cand_projects))

    req_certs = set(job["required_certifications"])
    pref_certs = set(job["preferred_certifications"])
    cand_certs = set(candidate["candidate_certifications"])
    if req_certs:
        cert_score = len(req_certs & cand_certs) / len(req_certs)
    elif pref_certs:
        cert_score = 0.5 + 0.5 * (len(pref_certs & cand_certs) / len(pref_certs))
    else:
        cert_score = 0.5 if cand_certs else 0.4

    semantic_score = _semantic_proxy(job, candidate)

    components = {
        "required_skill_match": round(req_match, 4),
        "preferred_skill_match": round(pref_match, 4),
        "experience_match": round(exp_score, 4),
        "project_relevance": round(proj_score, 4),
        "education_match": round(edu_score, 4),
        "certification_match": round(cert_score, 4),
        "semantic_similarity": round(semantic_score, 4),
    }

    weighted = (
        components["required_skill_match"] * COMPONENT_WEIGHTS["required_skill"] +
        components["preferred_skill_match"] * COMPONENT_WEIGHTS["preferred_skill"] +
        components["experience_match"] * COMPONENT_WEIGHTS["experience"] +
        components["project_relevance"] * COMPONENT_WEIGHTS["project"] +
        components["education_match"] * COMPONENT_WEIGHTS["education"] +
        components["certification_match"] * COMPONENT_WEIGHTS["certification"] +
        components["semantic_similarity"] * COMPONENT_WEIGHTS["semantic"]
    )
    score = round(max(0.0, min(1.0, weighted)) * 100, 2)
    return score, components


def _join_or_none(items):
    """Joins a list with ';'; uses an explicit 'NONE' sentinel for empty lists
    so an intentionally-empty optional field is never confused with a missing
    value when the CSV is read back (empty string round-trips as NaN)."""
    return ";".join(items) if items else "NONE"


def assign_label(score):
    for lo, hi, label, _name in LABEL_THRESHOLDS:
        if lo <= score < hi:
            return label
    return 4


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------
def build_job_candidate_counts(n_jobs, target_pairs, rng):
    counts = [rng.randint(6, 20) for _ in range(n_jobs)]
    diff = target_pairs - sum(counts)
    guard = 0
    while diff != 0 and guard < 200000:
        idx = rng.randrange(n_jobs)
        if diff > 0:
            counts[idx] += 1
            diff -= 1
        elif counts[idx] > 3:
            counts[idx] -= 1
            diff += 1
        guard += 1
    return counts


def sample_tiers(n, rng):
    return [rng.choices(TIERS, weights=TIER_WEIGHTS, k=1)[0] for _ in range(n)]


def load_real_it_resumes(path, min_chars=200):
    """Load Kaggle Resume Dataset rows filtered to INFORMATION-TECHNOLOGY."""
    if not path or not os.path.exists(path):
        log.info("No real resume file at %s — synthetic profiles only", path)
        return []
    raw = pd.read_csv(path)
    col_map = {c.lower(): c for c in raw.columns}
    text_col = col_map.get("resume_str") or col_map.get("resume") or col_map.get("text")
    cat_col = col_map.get("category")
    if not text_col:
        log.warning("Real resume CSV missing text column — skipping")
        return []
    if cat_col:
        mask = raw[cat_col].astype(str).str.upper().str.contains("INFORMATION-TECHNOLOGY")
        subset = raw.loc[mask, text_col]
    else:
        subset = raw[text_col]
    texts = []
    for txt in subset.fillna(""):
        cleaned = " ".join(str(txt).split())
        if len(cleaned) >= min_chars:
            texts.append(cleaned[:4000])
    log.info("Loaded %d IT resume texts from %s", len(texts), path)
    return texts


def generate_dataset(samples, seed, outdir, real_resume_texts=None, real_text_fraction=0.12):
    rng = random.Random(seed)
    real_resume_texts = real_resume_texts or []
    log.info("Generating SCREENWISE Model 2 (IT) dataset: %d pairs, seed=%d", samples, seed)
    if real_resume_texts:
        log.info("Real resume pool: %d IT profiles (up to %.0f%% of candidates)",
                 len(real_resume_texts), real_text_fraction * 100)

    n_jobs = max(500, min(1000, samples // 15))
    log.info("Target job count: %d", n_jobs)

    jobs = [generate_job(i + 1, rng) for i in range(n_jobs)]
    counts = build_job_candidate_counts(n_jobs, samples, rng)

    rows = []
    for job, n_cand in zip(jobs, counts):
        tiers = sample_tiers(n_cand, rng)
        for ci, tier in enumerate(tiers, start=1):
            cand = generate_candidate(job, ci, tier, rng)
            data_source = "synthetic"
            if real_resume_texts and rng.random() < real_text_fraction:
                cand = dict(cand)
                cand["candidate_profile_text"] = rng.choice(real_resume_texts)
                data_source = "real_kaggle"
            score, components = score_pair(job, cand)
            label = assign_label(score)
            row = {
                "job_id": job["job_id"],
                "job_title": job["job_title"],
                "seniority_level": job["seniority_level"],
                "job_description": job["job_description"],
                "required_skills": _join_or_none(job["required_skills"]),
                "preferred_skills": _join_or_none(job["preferred_skills"]),
                "minimum_experience_years": job["minimum_experience_years"],
                "preferred_experience_years": job["preferred_experience_years"],
                "required_education": job["required_education"],
                "preferred_education": job["preferred_education"],
                "required_certifications": _join_or_none(job["required_certifications"]),
                "preferred_certifications": _join_or_none(job["preferred_certifications"]),
                "required_project_types": _join_or_none(job["required_project_types"]),
                "technical_requirements": _join_or_none(job["technical_requirements"]),
                "responsibilities": _join_or_none(job["responsibilities"]),
                "soft_skill_requirements": _join_or_none(job["soft_skill_requirements"]),

                "candidate_id": cand["candidate_id"],
                "candidate_skills": _join_or_none(cand["candidate_skills"]),
                "candidate_education": cand["candidate_education"],
                "candidate_experience_years": cand["candidate_experience_years"],
                "candidate_job_titles": _join_or_none(cand["candidate_job_titles"]),
                "candidate_projects": _join_or_none(cand["candidate_projects"]),
                "candidate_certifications": _join_or_none(cand["candidate_certifications"]),
                "candidate_profile_text": cand["candidate_profile_text"],
                "candidate_experience_description": cand["candidate_experience_description"],
                "candidate_project_description": cand["candidate_project_description"],

                "required_skill_match": components["required_skill_match"],
                "preferred_skill_match": components["preferred_skill_match"],
                "experience_match": components["experience_match"],
                "project_relevance": components["project_relevance"],
                "education_match": components["education_match"],
                "certification_match": components["certification_match"],
                "semantic_similarity": components["semantic_similarity"],

                "relevance_score": score,
                "relevance_label": label,
                "match_tier": cand["_tier"],
                "candidate_archetype": cand["_archetype"],
                "data_source": data_source,
            }
            rows.append(row)

    df = pd.DataFrame(rows)
    assert len(df) == samples, f"Expected {samples} rows, got {len(df)}"

    # rank_within_job (1 = best match for that job)
    df["rank_within_job"] = df.groupby("job_id")["relevance_score"] \
        .rank(method="first", ascending=False).astype(int)

    os.makedirs(outdir, exist_ok=True)
    ranking_path = os.path.join(outdir, "ranking_dataset.csv")
    df.to_csv(ranking_path, index=False)
    log.info("Wrote %s (%d rows, %d cols)", ranking_path, *df.shape)

    return df, jobs


def build_pairwise_dataset(df, rng, max_pairs_per_job=5):
    rows = []
    for job_id, g in df.groupby("job_id"):
        g = g.reset_index(drop=True)
        n = len(g)
        if n < 2:
            continue
        n_pairs = min(max_pairs_per_job, n * (n - 1) // 2)
        seen = set()
        attempts = 0
        while len(seen) < n_pairs and attempts < n_pairs * 10:
            i, j = rng.sample(range(n), 2)
            key = tuple(sorted((i, j)))
            attempts += 1
            if key in seen:
                continue
            seen.add(key)
            a, b = g.loc[key[0]], g.loc[key[1]]
            preferred = a["candidate_id"] if a["relevance_score"] >= b["relevance_score"] else b["candidate_id"]
            rows.append({
                "job_id": job_id,
                "candidate_a_id": a["candidate_id"],
                "candidate_b_id": b["candidate_id"],
                "candidate_a_score": a["relevance_score"],
                "candidate_b_score": b["relevance_score"],
                "preferred_candidate": preferred,
            })
    return pd.DataFrame(rows)


def group_aware_split(df, seed, train_frac=0.70, val_frac=0.15):
    """Splits by job_id so an entire job's candidate pool stays in one split.
    This guarantees zero job-side leakage. Candidates are generated uniquely
    per job (candidate_id is job-scoped), so this also prevents duplicate
    (job, candidate) pairs from crossing splits."""
    job_ids = sorted(df["job_id"].unique())
    rng = random.Random(seed)
    rng.shuffle(job_ids)
    n = len(job_ids)
    n_train = int(n * train_frac)
    n_val = int(n * val_frac)
    train_jobs = set(job_ids[:n_train])
    val_jobs = set(job_ids[n_train:n_train + n_val])
    test_jobs = set(job_ids[n_train + n_val:])

    train_df = df[df["job_id"].isin(train_jobs)].reset_index(drop=True)
    val_df = df[df["job_id"].isin(val_jobs)].reset_index(drop=True)
    test_df = df[df["job_id"].isin(test_jobs)].reset_index(drop=True)
    return train_df, val_df, test_df, {
        "train_jobs": len(train_jobs), "val_jobs": len(val_jobs), "test_jobs": len(test_jobs),
    }


def main():
    parser = argparse.ArgumentParser(description="Generate SCREENWISE Model 2 IT ranking dataset")
    parser.add_argument("--samples", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--outdir", type=str, default="datasets/model2_it")
    parser.add_argument(
        "--real_candidates",
        type=str,
        default="",
        help="Optional Kaggle Resume.csv path; IT rows used as candidate_profile_text source",
    )
    parser.add_argument(
        "--real_jobs",
        type=str,
        default="",
        help="Optional job postings CSV with free-text descriptions (future use)",
    )
    parser.add_argument(
        "--real_text_fraction",
        type=float,
        default=0.12,
        help="Fraction of candidates that receive real resume profile text",
    )
    args = parser.parse_args()

    real_texts = load_real_it_resumes(args.real_candidates) if args.real_candidates else []
    if args.real_jobs:
        log.info("--real_jobs provided (%s); job phrasing pool hook reserved for future use", args.real_jobs)

    df, jobs = generate_dataset(
        args.samples, args.seed, args.outdir,
        real_resume_texts=real_texts,
        real_text_fraction=args.real_text_fraction,
    )

    rng = random.Random(args.seed + 1)
    pairwise_df = build_pairwise_dataset(df, rng)
    pairwise_path = os.path.join(args.outdir, "pairwise_ranking_dataset.csv")
    pairwise_df.to_csv(pairwise_path, index=False)
    log.info("Wrote %s (%d rows)", pairwise_path, len(pairwise_df))

    train_df, val_df, test_df, split_info = group_aware_split(df, args.seed)
    train_df.to_csv(os.path.join(args.outdir, "train.csv"), index=False)
    val_df.to_csv(os.path.join(args.outdir, "validation.csv"), index=False)
    test_df.to_csv(os.path.join(args.outdir, "test.csv"), index=False)
    log.info("Split: train=%d rows/%d jobs, val=%d rows/%d jobs, test=%d rows/%d jobs",
              len(train_df), split_info["train_jobs"], len(val_df), split_info["val_jobs"],
              len(test_df), split_info["test_jobs"])

    # sanity: no job_id appears in more than one split
    overlap_tv = set(train_df.job_id) & set(val_df.job_id)
    overlap_tt = set(train_df.job_id) & set(test_df.job_id)
    overlap_vt = set(val_df.job_id) & set(test_df.job_id)
    assert not (overlap_tv or overlap_tt or overlap_vt), "Job leakage detected across splits!"

    metadata = {
        "dataset_name": "SCREENWISE Model 2 - IT Candidate Ranking Dataset",
        "total_pairs": int(len(df)),
        "unique_jobs": int(df.job_id.nunique()),
        "unique_candidates": int(df.candidate_id.nunique()),
        "seed": args.seed,
        "label_thresholds": {name: [lo, hi] for lo, hi, _l, name in LABEL_THRESHOLDS},
        "component_weights": COMPONENT_WEIGHTS,
        "tier_distribution": df["match_tier"].value_counts().to_dict(),
        "archetype_distribution": df["candidate_archetype"].value_counts().to_dict(),
        "label_distribution": df["relevance_label"].value_counts().sort_index().to_dict(),
        "role_distribution": df["job_title"].value_counts().to_dict(),
        "seniority_distribution": df["seniority_level"].value_counts().to_dict(),
        "split": {
            "train_rows": int(len(train_df)), "val_rows": int(len(val_df)), "test_rows": int(len(test_df)),
            **split_info,
        },
        "data_source_distribution": df["data_source"].value_counts().to_dict() if "data_source" in df.columns else {},
        "real_candidates_file": args.real_candidates or None,
    }
    with open(os.path.join(args.outdir, "dataset_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    log.info("Wrote dataset_metadata.json")

    log.info("Done. Score range: min=%.2f max=%.2f mean=%.2f",
              df.relevance_score.min(), df.relevance_score.max(), df.relevance_score.mean())


if __name__ == "__main__":
    main()
