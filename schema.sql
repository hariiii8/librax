-- ============================================================
--  LibraX – Library Management System
--  Oracle SQL Setup Script
--  File: schema.sql  (place in librax/ root folder)
--  Run this in Oracle SQL Developer or SQL*Plus
-- ============================================================


-- ── STUDENTS TABLE ─────────────────────────────────────────
CREATE TABLE students (
    student_id      VARCHAR2(20)    PRIMARY KEY,       -- e.g. STU2024001
    full_name       VARCHAR2(100)   NOT NULL,
    email           VARCHAR2(100)   UNIQUE NOT NULL,
    phone           VARCHAR2(15),
    department      VARCHAR2(100),
    password_hash   VARCHAR2(64)    NOT NULL,          -- SHA-256 hex
    is_active       NUMBER(1)       DEFAULT 1,         -- 1=active, 0=inactive
    joined_date     DATE            DEFAULT SYSDATE,
    CONSTRAINT chk_student_active CHECK (is_active IN (0, 1))
);


-- ── STAFF TABLE ────────────────────────────────────────────
CREATE TABLE staff (
    employee_id     VARCHAR2(20)    PRIMARY KEY,       -- e.g. EMP1042
    full_name       VARCHAR2(100)   NOT NULL,
    email           VARCHAR2(100)   UNIQUE NOT NULL,
    phone           VARCHAR2(15),
    staff_role      VARCHAR2(30)    DEFAULT 'librarian', -- 'librarian' or 'admin'
    password_hash   VARCHAR2(64)    NOT NULL,
    is_active       NUMBER(1)       DEFAULT 1,
    joined_date     DATE            DEFAULT SYSDATE,
    CONSTRAINT chk_staff_active CHECK (is_active IN (0, 1)),
    CONSTRAINT chk_staff_role   CHECK (staff_role IN ('librarian', 'admin'))
);


-- ── BOOKS TABLE ────────────────────────────────────────────
CREATE TABLE books (
    book_id         NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    isbn            VARCHAR2(20)    UNIQUE NOT NULL,
    title           VARCHAR2(255)   NOT NULL,
    author          VARCHAR2(150)   NOT NULL,
    genre           VARCHAR2(50),
    publisher       VARCHAR2(100),
    publish_year    NUMBER(4),
    total_copies    NUMBER(3)       DEFAULT 1,
    available_copies NUMBER(3)      DEFAULT 1,
    added_by        VARCHAR2(20)    REFERENCES staff(employee_id),
    added_date      DATE            DEFAULT SYSDATE
);


-- ── ISSUE / RETURN TABLE ───────────────────────────────────
CREATE TABLE book_issues (
    issue_id        NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    book_id         NUMBER          REFERENCES books(book_id),
    student_id      VARCHAR2(20)    REFERENCES students(student_id),
    issued_by       VARCHAR2(20)    REFERENCES staff(employee_id),
    issue_date      DATE            DEFAULT SYSDATE,
    due_date        DATE            DEFAULT SYSDATE + 14,  -- 14 day loan period
    return_date     DATE,                                   -- NULL until returned
    status          VARCHAR2(20)    DEFAULT 'issued',       -- 'issued' | 'returned' | 'overdue'
    CONSTRAINT chk_issue_status CHECK (status IN ('issued', 'returned', 'overdue'))
);


-- ── FINES TABLE ────────────────────────────────────────────
CREATE TABLE fines (
    fine_id         NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    issue_id        NUMBER          REFERENCES book_issues(issue_id),
    student_id      VARCHAR2(20)    REFERENCES students(student_id),
    fine_amount     NUMBER(6,2)     NOT NULL,
    paid            NUMBER(1)       DEFAULT 0,
    paid_date       DATE,
    CONSTRAINT chk_fine_paid CHECK (paid IN (0, 1))
);


-- ── RESERVATIONS TABLE ─────────────────────────────────────
CREATE TABLE reservations (
    reservation_id  NUMBER          GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    book_id         NUMBER          REFERENCES books(book_id),
    student_id      VARCHAR2(20)    REFERENCES students(student_id),
    reserved_date   DATE            DEFAULT SYSDATE,
    status          VARCHAR2(20)    DEFAULT 'pending',  -- 'pending' | 'fulfilled' | 'cancelled'
    CONSTRAINT chk_res_status CHECK (status IN ('pending', 'fulfilled', 'cancelled'))
);


-- ============================================================
--  SAMPLE DATA  (for testing login)
--  Password for all demo accounts: "password123"
--  SHA-256 of "password123" = ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f
-- ============================================================

INSERT INTO students (student_id, full_name, email, department, password_hash)
VALUES ('STU2024001', 'Arjun Sharma',   'arjun@college.edu',  'Computer Science',
        'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f');

INSERT INTO students (student_id, full_name, email, department, password_hash)
VALUES ('STU2024002', 'Priya Nair',     'priya@college.edu',  'Electronics',
        'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f');

INSERT INTO staff (employee_id, full_name, email, staff_role, password_hash)
VALUES ('EMP1042', 'Dr. Meena Krishnan', 'meena@college.edu', 'admin',
        'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f');

INSERT INTO staff (employee_id, full_name, email, staff_role, password_hash)
VALUES ('EMP2001', 'Ravi Kumar',        'ravi@college.edu',   'librarian',
        'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f');

COMMIT;
