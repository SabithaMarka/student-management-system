-- =====================================================================
--  Migration 001: upgrade the basic Student Management System to the
--  Smart Student Management & Academic Portal.
-- ---------------------------------------------------------------------
--  Safe and idempotent: it can be run more than once.
--  - Adds the `role` column to `students` (if missing).
--  - Creates the new academic tables (if missing).
--  - Inserts the admin account and sample academic data (INSERT IGNORE).
--  - Does NOT drop or modify existing student rows.
--
--  Run with:  mysql -u root -p student_management < migrations/001_upgrade_portal.sql
-- =====================================================================

USE student_management;

-- 1) Add role column to students (only if it does not already exist).
SET @col := (SELECT COUNT(*) FROM information_schema.columns
             WHERE table_schema = DATABASE() AND table_name = 'students' AND column_name = 'role');
SET @sql := IF(@col = 0,
  'ALTER TABLE students ADD COLUMN role ENUM(''student'',''admin'') NOT NULL DEFAULT ''student''',
  'SELECT ''role column already exists'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2) Ensure all existing rows are students (admin is seeded below).
UPDATE students SET role = 'student' WHERE role IS NULL OR role = '';

-- 3) New academic tables (if not already present).

-- -------------------------------------------------------------------
-- subjects
-- -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS subjects (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  code       VARCHAR(30)  NOT NULL UNIQUE,
  name       VARCHAR(120) NOT NULL,
  department VARCHAR(80)  NOT NULL,
  year       TINYINT      NOT NULL,
  semester   TINYINT      NOT NULL,
  credits    TINYINT      NOT NULL DEFAULT 3,
  faculty    VARCHAR(100),
  created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------------
-- attendance  (one row per student per subject)
-- -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS attendance (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  student_id      INT NOT NULL,
  subject_id      INT NOT NULL,
  total_classes   INT NOT NULL DEFAULT 0,
  present_classes INT NOT NULL DEFAULT 0,
  UNIQUE KEY uniq_attendance (student_id, subject_id),
  CONSTRAINT fk_att_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  CONSTRAINT fk_att_subject FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

-- -------------------------------------------------------------------
-- marks  (one row per student per subject; each component is 0-100)
-- -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marks (
  id               INT AUTO_INCREMENT PRIMARY KEY,
  student_id       INT NOT NULL,
  subject_id       INT NOT NULL,
  internal_marks   INT NOT NULL DEFAULT 0,
  assignment_marks INT NOT NULL DEFAULT 0,
  semester_marks   INT NOT NULL DEFAULT 0,
  UNIQUE KEY uniq_marks (student_id, subject_id),
  CONSTRAINT fk_marks_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  CONSTRAINT fk_marks_subject FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

-- -------------------------------------------------------------------
-- assignments
-- -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS assignments (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  title       VARCHAR(150) NOT NULL,
  description TEXT,
  subject_id  INT NOT NULL,
  due_date    DATE NOT NULL,
  status      ENUM('open','closed') NOT NULL DEFAULT 'open',
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_asg_subject FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

-- -------------------------------------------------------------------
-- announcements
-- -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS announcements (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  title       VARCHAR(200) NOT NULL,
  description TEXT,
  category    VARCHAR(40) NOT NULL DEFAULT 'General',
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- 4) Seed the admin account (INSERT IGNORE so re-running is safe).
INSERT IGNORE INTO students
  (student_id, name, email, phone, department, year, password_hash, role)
VALUES
  ('admin', 'System Admin', 'admin@portal.local', '0000000000', 'Administration', 1, 'scrypt:32768:8:1$gXfD287WFODNiZIs$000b82fe65f914519aba41de9fe6ce33913459eda39c1078fcb142778d843bcdf132438fa45fd675b6c50faa5da4d8aa777b5f0fae468c992a358b25722d795b', 'admin');


-- 5) Seed sample academic data (subjects, attendance, marks, assignments,
--    announcements). These reference students 1..3 and subjects 1..5.
INSERT IGNORE INTO subjects (code, name, department, year, semester, credits, faculty) VALUES
  ('CS101', 'Programming Fundamentals', 'Computer Science', 1, 1, 4, 'Dr. Rao'),
  ('CS102', 'Data Structures', 'Computer Science', 1, 2, 3, 'Prof. Mehta'),
  ('IT201', 'Computer Networks', 'Information Technology', 2, 3, 4, 'Dr. Khan'),
  ('IT202', 'Web Development', 'Information Technology', 2, 3, 3, 'Prof. Sharma'),
  ('EC301', 'Digital Electronics', 'Electronics & Communication', 3, 5, 4, 'Dr. Iyer');
INSERT IGNORE INTO attendance (student_id, subject_id, total_classes, present_classes) VALUES
  (1, 1, 40, 38),
  (1, 2, 40, 28),
  (2, 3, 40, 36),
  (2, 4, 40, 30),
  (3, 5, 40, 25);
INSERT IGNORE INTO marks (student_id, subject_id, internal_marks, assignment_marks, semester_marks) VALUES
  (1, 1, 85, 80, 90),
  (1, 2, 60, 55, 50),
  (2, 3, 78, 75, 80),
  (2, 4, 70, 72, 68),
  (3, 5, 65, 60, 55);
INSERT IGNORE INTO assignments (title, description, subject_id, due_date, status) VALUES
  ('Lab Report 1', 'First lab report on programming fundamentals.', 1, '2026-10-30', 'open'),
  ('Network Topology Project', 'Design a small campus network topology.', 3, '2026-11-10', 'open'),
  ('Digital Circuits Worksheet', 'Past worksheet on combinational circuits.', 5, '2026-10-20', 'closed');
INSERT IGNORE INTO announcements (title, description, category) VALUES
  ('Welcome to the Portal', 'Welcome to the Smart Student Management & Academic Portal. Check your dashboard regularly.', 'General'),
  ('Mid-term Examinations Schedule', 'Mid-term examinations begin next month. Please check your subjects for details.', 'Exam'),
  ('Diwali Holiday Notice', 'The institute remains closed for the Diwali festival. Classes resume soon.', 'Holiday');

