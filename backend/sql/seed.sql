-- Seed admin + sample HR (password for both: Password123!)
-- bcrypt hash generated for Password123!

USE cv_screening;

INSERT INTO users (id, email, password_hash, role, is_active) VALUES
  ('11111111-1111-1111-1111-111111111111', 'admin@cvscreening.local',
   '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', 'admin', 1),
  ('22222222-2222-2222-2222-222222222222', 'hr@cvscreening.local',
   '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', 'hr', 1)
ON DUPLICATE KEY UPDATE email = VALUES(email);

INSERT INTO hr_managers (id, user_id, full_name, company, phone) VALUES
  ('33333333-3333-3333-3333-333333333333', '22222222-2222-2222-2222-222222222222',
   'Sample HR Manager', 'Demo Recruitment Ltd', '+94 77 000 0000')
ON DUPLICATE KEY UPDATE full_name = VALUES(full_name);
