-- =====================================================================
--  College Student Management System – database schema
-- =====================================================================
--  Full fresh-install schema. Safe to run multiple times.
--  Every account password: password123
--
--  Seed accounts
--  ─────────────
--  Admin  :  student_id=admin   / email=admin@portal.local
--  Student:  STU001 / alice@example.com
--  Student:  STU002 / bob@example.com
--  Student:  STU003 / carol@example.com  (att shortage + backlogs)
-- =====================================================================

CREATE DATABASE IF NOT EXISTS student_management
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE student_management;

-- ── students (one table, role column separates admin vs student) ─────────────
CREATE TABLE IF NOT EXISTS students (
  id               INT AUTO_INCREMENT PRIMARY KEY,
  student_id       VARCHAR(30)  NOT NULL UNIQUE,
  name             VARCHAR(100) NOT NULL,
  email            VARCHAR(120) NOT NULL UNIQUE,
  phone            VARCHAR(20)  NOT NULL,
  department       VARCHAR(80)  NOT NULL,
  course           VARCHAR(80)  NULL,
  year             TINYINT      NOT NULL,
  semester         TINYINT      NULL,
  section          VARCHAR(10)  NULL,
  cgpa             DECIMAL(4,2) NULL,
  backlogs         TINYINT      NOT NULL DEFAULT 0,
  backlog_details  TEXT         NULL,
  attendance_pct   DECIMAL(5,2) NULL,
  total_fee        DECIMAL(10,2) NOT NULL DEFAULT 0,
  amount_paid      DECIMAL(10,2) NOT NULL DEFAULT 0,
  amount_due       DECIMAL(10,2) NOT NULL DEFAULT 0,
  payment_status   ENUM('Fully Paid','Half Paid','Partially Paid','Due','Pending')
                   NOT NULL DEFAULT 'Pending',
  roll_number      VARCHAR(30)  NULL,
  gender           VARCHAR(10)  NULL,
  dob              DATE         NULL,
  address          TEXT         NULL,
  password_hash    VARCHAR(255) NOT NULL,
  role             ENUM('student','admin') NOT NULL DEFAULT 'student',
  created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY idx_roll_number (roll_number)
);

-- ── Seed accounts ────────────────────────────────────────────────────────────
INSERT IGNORE INTO students
  (student_id, name, email, phone,
   department, course, year, semester, section,
   cgpa, backlogs, backlog_details, attendance_pct,
   total_fee, amount_paid, amount_due, payment_status,
   gender, dob, address,
   password_hash, role)
VALUES
  ('STU001', 'Alice Johnson', 'alice@example.com', '9876543210',
   'Computer Science Engineering', 'B.Tech', 1, 2, 'A',
   7.85, 1, 'Data Structures (CS201)', 84.5,
   80000, 40000, 40000, 'Half Paid',
   'Female', '2004-05-14', '12, MG Road, Bangalore - 560001',
   'scrypt:32768:8:1$Zdcd6x2KjiwUhKjF$14a93486c78c6ea5ba8ed9219de0717dbcef1cbf2539a65a3b9cbfcb873436895397cde636284d3af88421d8e866daf0bc2f06aeab18e402710886eef7b992e1', 'student'),
  ('STU002', 'Bob Smith', 'bob@example.com', '9123456780',
   'Information Technology', 'B.Tech', 2, 4, 'B',
   8.2, 0, NULL, 91.0,
   80000, 80000, 0, 'Fully Paid',
   'Male', '2003-07-22', NULL,
   'scrypt:32768:8:1$uLVI2wRUcAsXT0wh$612f9578b6b1dd1ac1e1c44c0635317ff4ca1df3a8a0322d739cf5e8eed2c853babff87696c6ffd4cc4870d8c00b30376e42b211800683217b8aa74d8b3dafdf', 'student'),
  ('STU003', 'Carol Davis', 'carol@example.com', '9988776655',
   'Electronics & Communication', 'B.Tech', 3, 6, 'A',
   6.5, 2, 'OS Lab, DBMS', 68.0,
   80000, 20000, 60000, 'Pending',
   'Female', '2003-03-10', NULL,
   'scrypt:32768:8:1$niuZchTpzLAYbOFX$feed6d6ee52ccd8230a1239ccfd8a11be6b4567750f5b00673479ef1011be3c51940f93962d3e2a29aef36b7f5f062e78db1aec62c8242bb72855f014da11eec', 'student'),
  ('admin', 'System Admin', 'admin@portal.local', '0000000000',
   'Administration', NULL, 1, NULL, NULL,
   NULL, 0, NULL, NULL,
   0, 0, 0, 'Pending',
   NULL, NULL, NULL,
   'scrypt:32768:8:1$6lPGZtYcxc7YwCx3$0db0864d2f07651ffa9533e3f982ec2e79e10edeb23a24d499bca06d48d1165332bcaa804bb12861aa43f2e6328f9d3f5365356cb4c2e57dd0bab527132460b2', 'admin');
