-- Phase 4/5 additive migration (safe to run on existing DB)
USE cv_screening;

CREATE TABLE IF NOT EXISTS interviews (
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
