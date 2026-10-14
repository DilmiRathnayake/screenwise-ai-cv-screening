"""
taxonomy.py
Controlled IT skill taxonomy, skill-relationship graph, role definitions and
role -> scoring-weight map for the SCREENWISE Model 2 (IT Candidate Ranking) dataset.

All structures here are the single source of truth used by:
  - generate_model2_it_dataset.py
  - validate_model2_dataset.py
  - prepare_model2_features.py
"""

import random

# --------------------------------------------------------------------------
# 1. SKILL TAXONOMY (grouped by category)
# --------------------------------------------------------------------------
CATEGORY_SKILLS = {
    "programming": ["Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#",
                     "PHP", "Kotlin", "Dart", "Go", "Ruby", "Swift", "Rust"],
    "frontend": ["HTML", "CSS", "JavaScript", "TypeScript", "React", "Next.js",
                 "Angular", "Vue.js", "Svelte", "Tailwind CSS", "Bootstrap",
                 "Material UI", "Redux", "React Query"],
    "backend": ["Node.js", "Express.js", "NestJS", "Django", "Flask", "FastAPI",
                "Laravel", "Spring", "Spring Boot", "ASP.NET", ".NET", "Ruby on Rails"],
    "database": ["MySQL", "PostgreSQL", "MongoDB", "SQL Server", "Oracle", "SQLite",
                 "Redis", "Firebase", "Supabase", "DynamoDB"],
    "cloud": ["AWS", "Azure", "Google Cloud", "Firebase", "AWS Lambda", "EC2", "S3",
              "Cloud Functions"],
    "devops": ["Docker", "Kubernetes", "Jenkins", "GitHub Actions", "GitLab CI/CD",
               "CI/CD", "Terraform", "Ansible", "Linux", "Nginx"],
    "testing": ["Selenium", "Cypress", "Playwright", "Jest", "JUnit", "PyTest",
                "Postman", "REST API Testing", "Unit Testing", "Integration Testing",
                "Automation Testing", "Manual Testing"],
    "data": ["Python", "Pandas", "NumPy", "SQL", "Power BI", "Tableau", "Excel",
             "Data Visualization", "Statistics"],
    "ai_ml": ["Machine Learning", "Deep Learning", "NLP", "Computer Vision",
              "Scikit-learn", "TensorFlow", "PyTorch", "Transformers", "spaCy", "OpenCV"],
    "mobile": ["Flutter", "Dart", "Android", "Kotlin", "Java", "React Native", "Swift"],
    "ui_ux": ["Figma", "Adobe XD", "Wireframing", "Prototyping", "User Research",
              "Usability Testing", "Design Systems", "Responsive Design"],
    "swe": ["OOP", "SOLID", "Design Patterns", "Data Structures", "Algorithms",
            "System Design", "REST APIs", "GraphQL", "Microservices", "Git", "GitHub",
            "Agile", "Scrum", "Jira"],
    "security": ["Network Security", "OWASP", "Penetration Testing", "SIEM",
                 "Authentication", "Authorization", "JWT", "OAuth", "Cybersecurity",
                 "Cryptography"],
}

ALL_SKILLS = sorted({s for skills in CATEGORY_SKILLS.values() for s in skills})

# --------------------------------------------------------------------------
# 2. SKILL RELATIONSHIP GRAPH (for the semantic-proxy signal only —
#    NOT used to fabricate required-skill matches)
# --------------------------------------------------------------------------
SKILL_RELATIONS = {
    "React": ["JavaScript", "TypeScript", "Next.js", "Redux", "React Query"],
    "Next.js": ["React", "JavaScript", "TypeScript"],
    "Node.js": ["JavaScript", "Express.js", "NestJS"],
    "Express.js": ["Node.js", "JavaScript"],
    "NestJS": ["Node.js", "TypeScript"],
    "Django": ["Python", "Flask", "FastAPI"],
    "Flask": ["Python", "Django"],
    "FastAPI": ["Python", "Django", "Flask"],
    "Laravel": ["PHP"],
    "Spring Boot": ["Java", "Spring"],
    "Spring": ["Java", "Spring Boot"],
    "ASP.NET": ["C#", ".NET"],
    ".NET": ["C#", "ASP.NET"],
    "Flutter": ["Dart"],
    "React Native": ["JavaScript", "TypeScript", "React"],
    "TensorFlow": ["Python", "Machine Learning", "Deep Learning"],
    "PyTorch": ["Python", "Machine Learning", "Deep Learning"],
    "Pandas": ["Python", "NumPy", "Data Visualization"],
    "PostgreSQL": ["SQL", "MySQL"],
    "MySQL": ["SQL", "PostgreSQL"],
    "Docker": ["Kubernetes", "DevOps", "CI/CD"],
    "Kubernetes": ["Docker", "DevOps"],
    "Jenkins": ["CI/CD", "GitHub Actions", "GitLab CI/CD"],
    "GraphQL": ["REST APIs", "Node.js"],
    "AWS": ["Azure", "Google Cloud", "EC2", "S3", "AWS Lambda"],
}


def related_skills(skill):
    return SKILL_RELATIONS.get(skill, [])


# --------------------------------------------------------------------------
# 3. SENIORITY -> EXPERIENCE RANGES (years)
# --------------------------------------------------------------------------
SENIORITY_EXPERIENCE = {
    "Intern":     (0, 0),
    "Trainee":    (0, 1),
    "Junior":     (0, 2),
    "Associate":  (1, 3),
    "Mid-level":  (2, 5),
    "Senior":     (5, 9),
    "Lead":       (6, 12),
}
SENIORITY_ORDER = list(SENIORITY_EXPERIENCE.keys())

EDUCATION_LEVELS = [
    "No formal degree", "Diploma", "Associate Degree", "Bachelor's Degree",
    "Bachelor's Degree (related field)", "Bachelor's Degree (unrelated field)",
    "Master's Degree", "PhD",
]
EDUCATION_RANK = {e: i for i, e in enumerate(EDUCATION_LEVELS)}

CERTIFICATIONS_BY_CATEGORY = {
    "cloud": ["AWS Certified Solutions Architect", "AWS Certified Developer",
              "Microsoft Azure Fundamentals (AZ-900)", "Google Cloud Associate Engineer"],
    "devops": ["Certified Kubernetes Administrator (CKA)", "Docker Certified Associate",
               "HashiCorp Terraform Associate"],
    "security": ["CompTIA Security+", "Certified Ethical Hacker (CEH)", "CISSP",
                 "OSCP"],
    "data": ["Google Data Analytics Certificate", "Microsoft Power BI Data Analyst"],
    "ai_ml": ["TensorFlow Developer Certificate", "DeepLearning.AI ML Specialization"],
    "testing": ["ISTQB Certified Tester Foundation Level"],
    "swe": ["Scrum Master (CSM)", "PMI-ACP"],
    "database": ["Oracle Certified Database Associate", "Microsoft SQL Server Certification"],
    "ui_ux": ["Google UX Design Certificate", "Certified Usability Analyst"],
    "network": ["Cisco CCNA", "CompTIA Network+"],
}

PROJECT_TYPES_BY_CATEGORY = {
    "frontend": ["e-commerce storefront UI", "admin dashboard", "portfolio website",
                 "responsive landing page", "progressive web app"],
    "backend": ["REST API service", "authentication microservice", "payment gateway integration",
                "order-management backend", "internal tooling API"],
    "database": ["data migration pipeline", "reporting schema redesign", "query optimization project"],
    "cloud": ["cloud infrastructure migration", "serverless functions deployment", "multi-region deployment"],
    "devops": ["CI/CD pipeline setup", "containerized deployment", "infrastructure-as-code rollout"],
    "testing": ["automated regression suite", "end-to-end test framework", "API test harness"],
    "data": ["sales dashboard", "data cleaning pipeline", "exploratory data analysis report"],
    "ai_ml": ["churn-prediction model", "image classification model", "chatbot with NLP",
              "recommendation engine"],
    "mobile": ["cross-platform mobile app", "Android utility app", "e-commerce mobile app"],
    "ui_ux": ["mobile app redesign", "usability study", "design system", "onboarding flow redesign"],
    "security": ["vulnerability assessment", "network security audit", "penetration test report"],
    "swe": ["microservices architecture", "internal developer tool", "system design document"],
}

# --------------------------------------------------------------------------
# 4. ROLE DEFINITIONS
#    Each role has: category weights for scoring (must sum to ~1.0 across
#    the components used in scoring), and which taxonomy categories its
#    required/preferred skills are drawn from.
# --------------------------------------------------------------------------
ROLES = {
    "Software Engineer":            {"primary": ["swe", "programming"], "secondary": ["backend", "database"]},
    "Software Developer":           {"primary": ["programming", "swe"], "secondary": ["backend", "frontend"]},
    "Full Stack Developer":         {"primary": ["frontend", "backend"], "secondary": ["database", "swe"]},
    "Frontend Developer":           {"primary": ["frontend"], "secondary": ["swe", "ui_ux"]},
    "Backend Developer":            {"primary": ["backend", "database"], "secondary": ["swe", "cloud"]},
    "React Developer":              {"primary": ["frontend"], "secondary": ["swe"]},
    "Next.js Developer":            {"primary": ["frontend"], "secondary": ["swe", "cloud"]},
    "Node.js Developer":            {"primary": ["backend"], "secondary": ["database", "swe"]},
    "Java Developer":               {"primary": ["backend", "programming"], "secondary": ["database", "swe"]},
    "Python Developer":             {"primary": ["backend", "programming"], "secondary": ["database", "swe"]},
    "C# Developer":                 {"primary": ["backend", "programming"], "secondary": ["database", "swe"]},
    ".NET Developer":               {"primary": ["backend"], "secondary": ["database", "swe"]},
    "PHP Developer":                {"primary": ["backend", "programming"], "secondary": ["database"]},
    "Laravel Developer":            {"primary": ["backend"], "secondary": ["database", "frontend"]},
    "Mobile Application Developer": {"primary": ["mobile"], "secondary": ["swe", "backend"]},
    "Android Developer":            {"primary": ["mobile"], "secondary": ["swe"]},
    "Flutter Developer":            {"primary": ["mobile"], "secondary": ["swe"]},
    "React Native Developer":       {"primary": ["mobile", "frontend"], "secondary": ["swe"]},
    "DevOps Engineer":              {"primary": ["devops", "cloud"], "secondary": ["swe"]},
    "Cloud Engineer":               {"primary": ["cloud"], "secondary": ["devops", "swe"]},
    "Cloud/DevOps Engineer":        {"primary": ["cloud", "devops"], "secondary": ["swe"]},
    "Data Analyst":                 {"primary": ["data"], "secondary": ["database"]},
    "Data Scientist":               {"primary": ["ai_ml", "data"], "secondary": ["swe"]},
    "Machine Learning Engineer":    {"primary": ["ai_ml"], "secondary": ["swe", "cloud"]},
    "AI Engineer":                  {"primary": ["ai_ml"], "secondary": ["backend", "cloud"]},
    "NLP Engineer":                 {"primary": ["ai_ml"], "secondary": ["data"]},
    "QA Engineer":                  {"primary": ["testing"], "secondary": ["swe"]},
    "Software QA Engineer":         {"primary": ["testing"], "secondary": ["swe"]},
    "Automation Tester":            {"primary": ["testing"], "secondary": ["swe"]},
    "Manual Tester":                {"primary": ["testing"], "secondary": []},
    "Cybersecurity Analyst":        {"primary": ["security"], "secondary": ["devops"]},
    "Cybersecurity Engineer":       {"primary": ["security"], "secondary": ["devops", "cloud"]},
    "Network Engineer":             {"primary": ["security", "devops"], "secondary": []},
    "System Administrator":         {"primary": ["devops"], "secondary": ["security", "cloud"]},
    "Database Administrator":       {"primary": ["database"], "secondary": ["cloud"]},
    "Data Engineer":                {"primary": ["data", "cloud"], "secondary": ["backend", "database"]},
    "UI/UX Designer":               {"primary": ["ui_ux"], "secondary": ["frontend"]},
    "Product Designer":             {"primary": ["ui_ux"], "secondary": ["frontend"]},
    "Technical Support Engineer":   {"primary": ["devops"], "secondary": ["database", "security"]},
    "IT Support Engineer":          {"primary": ["devops"], "secondary": ["database"]},
    "Solutions Engineer":           {"primary": ["cloud", "backend"], "secondary": ["swe"]},
    "Software Architect":           {"primary": ["swe", "backend"], "secondary": ["cloud", "devops"]},
}

ROLE_TITLES = list(ROLES.keys())


def role_required_skill_pool(role):
    cats = ROLES[role]["primary"]
    pool = set()
    for c in cats:
        pool.update(CATEGORY_SKILLS[c])
    return sorted(pool)


def role_preferred_skill_pool(role):
    cats = ROLES[role]["secondary"]
    pool = set()
    for c in cats:
        pool.update(CATEGORY_SKILLS[c])
    # remove anything already required
    pool -= set(role_required_skill_pool(role))
    return sorted(pool)


def role_categories(role):
    return ROLES[role]["primary"] + ROLES[role]["secondary"]
