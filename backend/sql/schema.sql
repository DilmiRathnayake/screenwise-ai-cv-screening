-- CV Screening System — Phase 2 normalized schema
-- MySQL 8.0+

CREATE DATABASE IF NOT EXISTS cv_screening
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE cv_screening;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS interviews;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS ranking_results;
DROP TABLE IF EXISTS applications;
DROP TABLE IF EXISTS cv_files;
DROP TABLE IF EXISTS candidate_skills;
DROP TABLE IF EXISTS candidates;
DROP TABLE IF EXISTS job_skills;
DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS hr_managers;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE users (
  id            CHAR(36)     NOT NULL PRIMARY KEY,
  email         VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role          ENUM('admin', 'hr', 'candidate') NOT NULL DEFAULT 'hr',
  is_active     TINYINT(1)   NOT NULL DEFAULT 1,
  created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB;

CREATE TABLE hr_managers (
  id         CHAR(36)     NOT NULL PRIMARY KEY,
  user_id    CHAR(36)     NOT NULL,
  full_name  VARCHAR(255) NOT NULL,
  company    VARCHAR(255) NULL,
  phone      VARCHAR(50)  NULL,
  created_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_hr_user (user_id),
  CONSTRAINT fk_hr_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE skills (
  id         INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name       VARCHAR(120) NOT NULL,
  normalized VARCHAR(120) NOT NULL,
  created_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_skills_normalized (normalized)
) ENGINE=InnoDB;

CREATE TABLE jobs (
  id                        CHAR(36)      NOT NULL PRIMARY KEY,
  hr_manager_id             CHAR(36)      NOT NULL,
  title                     VARCHAR(255)  NOT NULL,
  description               TEXT          NOT NULL,
  minimum_experience        DECIMAL(4,1)  NOT NULL DEFAULT 0,
  education_level           VARCHAR(100)  NULL,
  industry                  VARCHAR(50)   NOT NULL DEFAULT 'default',
  required_certifications   JSON          NULL,
  ranking_weights           JSON          NOT NULL,
  communication_importance  DECIMAL(3,2)  NULL,
  status                    ENUM('draft', 'active', 'closed') NOT NULL DEFAULT 'active',
  created_at                TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at                TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_jobs_hr (hr_manager_id),
  KEY idx_jobs_status (status),
  KEY idx_jobs_industry (industry),
  CONSTRAINT fk_jobs_hr FOREIGN KEY (hr_manager_id) REFERENCES hr_managers(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE job_skills (
  job_id   CHAR(36)     NOT NULL,
  skill_id INT UNSIGNED NOT NULL,
  PRIMARY KEY (job_id, skill_id),
  CONSTRAINT fk_js_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
  CONSTRAINT fk_js_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE candidates (
  id                    CHAR(36)      NOT NULL PRIMARY KEY,
  full_name             VARCHAR(255)  NULL,
  email                 VARCHAR(255)  NULL,
  phone                 VARCHAR(50)   NULL,
  address               VARCHAR(500)  NULL,
  linkedin              VARCHAR(500)  NULL,
  github                VARCHAR(500)  NULL,
  portfolio             VARCHAR(500)  NULL,
  years_of_experience   DECIMAL(4,1)  NULL,
  communication_score   DECIMAL(5,4)  NOT NULL DEFAULT 0.5000,
  education_json        JSON          NULL,
  experience_json       JSON          NULL,
  projects_json         JSON          NULL,
  certifications_json   JSON          NULL,
  languages_json        JSON          NULL,
  publications_json     JSON          NULL,
  awards_json           JSON          NULL,
  references_json       JSON          NULL,
  soft_skills_json      JSON          NULL,
  raw_text              MEDIUMTEXT    NULL,
  extraction_meta       JSON          NULL,
  created_at            TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at            TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_candidates_email (email)
) ENGINE=InnoDB;

CREATE TABLE candidate_skills (
  candidate_id CHAR(36)     NOT NULL,
  skill_id     INT UNSIGNED NOT NULL,
  skill_type   ENUM('technical', 'soft') NOT NULL DEFAULT 'technical',
  PRIMARY KEY (candidate_id, skill_id, skill_type),
  CONSTRAINT fk_cs_candidate FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
  CONSTRAINT fk_cs_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE cv_files (
  id                 CHAR(36)     NOT NULL PRIMARY KEY,
  candidate_id       CHAR(36)     NULL,
  original_filename  VARCHAR(255) NOT NULL,
  stored_filename    VARCHAR(255) NOT NULL,
  mime_type          VARCHAR(120) NULL,
  file_path          VARCHAR(500) NOT NULL,
  file_size_bytes    INT UNSIGNED NOT NULL DEFAULT 0,
  extraction_status  ENUM('pending', 'success', 'failed') NOT NULL DEFAULT 'pending',
  extraction_error   TEXT         NULL,
  created_at         TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_cv_candidate (candidate_id),
  CONSTRAINT fk_cv_candidate FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE applications (
  id           CHAR(36) NOT NULL PRIMARY KEY,
  job_id       CHAR(36) NOT NULL,
  candidate_id CHAR(36) NOT NULL,
  cv_file_id   CHAR(36) NULL,
  status       ENUM('uploaded', 'processed', 'shortlisted', 'rejected') NOT NULL DEFAULT 'uploaded',
  created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_application_job_candidate (job_id, candidate_id),
  KEY idx_app_job (job_id),
  KEY idx_app_status (status),
  CONSTRAINT fk_app_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
  CONSTRAINT fk_app_candidate FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
  CONSTRAINT fk_app_cv FOREIGN KEY (cv_file_id) REFERENCES cv_files(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE ranking_results (
  id                    CHAR(36)      NOT NULL PRIMARY KEY,
  application_id        CHAR(36)      NOT NULL,
  job_id                CHAR(36)      NOT NULL,
  candidate_score       DECIMAL(8,4)  NOT NULL,
  matching_percentage   DECIMAL(6,2)  NOT NULL,
  ranking_position      INT UNSIGNED  NOT NULL,
  semantic_similarity   DECIMAL(8,4)  NULL,
  ranking_explanation   TEXT          NULL,
  criterion_scores      JSON          NULL,
  weights_used          JSON          NULL,
  created_at            TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_rank_application (application_id),
  KEY idx_rank_job_pos (job_id, ranking_position),
  CONSTRAINT fk_rank_app FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
  CONSTRAINT fk_rank_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Stub for Phase interview automation
CREATE TABLE notifications (
  id           CHAR(36)     NOT NULL PRIMARY KEY,
  user_id      CHAR(36)     NULL,
  candidate_id CHAR(36)     NULL,
  type         VARCHAR(50)  NOT NULL,
  title        VARCHAR(255) NOT NULL,
  body         TEXT         NULL,
  is_read      TINYINT(1)   NOT NULL DEFAULT 0,
  created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_notif_user (user_id),
  CONSTRAINT fk_notif_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
  CONSTRAINT fk_notif_candidate FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE interviews (
  id              CHAR(36) NOT NULL PRIMARY KEY,
  application_id  CHAR(36) NOT NULL,
  job_id          CHAR(36) NOT NULL,
  candidate_id    CHAR(36) NOT NULL,
  scheduled_at    DATETIME NOT NULL,
  duration_minutes INT UNSIGNED NOT NULL DEFAULT 45,
  mode            ENUM('online', 'onsite', 'phone') NOT NULL DEFAULT 'online',
  meeting_link    VARCHAR(500) NULL,
  location        VARCHAR(255) NULL,
  status          ENUM('scheduled', 'rescheduled', 'completed', 'cancelled', 'no_show')
                  NOT NULL DEFAULT 'scheduled',
  notes           TEXT NULL,
  calendar_event_id VARCHAR(255) NULL,
  n8n_workflow_ref  VARCHAR(255) NULL,
  created_by      CHAR(36) NULL,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_interview_job (job_id),
  KEY idx_interview_candidate (candidate_id),
  KEY idx_interview_scheduled (scheduled_at),
  CONSTRAINT fk_interview_app FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
  CONSTRAINT fk_interview_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
  CONSTRAINT fk_interview_candidate FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
) ENGINE=InnoDB;
