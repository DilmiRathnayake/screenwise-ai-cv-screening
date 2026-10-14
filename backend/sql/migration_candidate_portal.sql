-- Candidate portal: allow candidate role on users table
USE cv_screening;

ALTER TABLE users
  MODIFY role ENUM('admin', 'hr', 'candidate') NOT NULL DEFAULT 'hr';
