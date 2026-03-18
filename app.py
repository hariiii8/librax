# ============================================================
#  LibraX – Library Management System
#  Flask Backend with Oracle SQL
#  File: app.py  (place in your librax/ root folder)
# ============================================================

import oracledb
import hashlib
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'librax_secret_key_change_me_2024'
app.permanent_session_lifetime = timedelta(days=30)

# ============================================================
#  ORACLE DATABASE CONNECTION
# ============================================================
DB_CONFIG = {
    "user":     "system",
    "password": "database",
    "dsn":      "localhost:1521/XE",
}

def get_db_connection():
    return oracledb.connect(
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        dsn=DB_CONFIG["dsn"]
    )

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ============================================================
#  DECORATORS
# ============================================================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def staff_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'staff':
            return redirect(url_for('student_dashboard'))
        return f(*args, **kwargs)
    return decorated


# ============================================================
#  PAGE ROUTES
# ============================================================

@app.route('/')
def home():
    if 'user_id' in session:
        if session.get('role') == 'staff':
            return redirect(url_for('staff_dashboard'))
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/student-dashboard')
@login_required
def student_dashboard():
    return render_template('student_dashboard.html')

@app.route('/staff-dashboard')
@staff_required
def staff_dashboard():
    return render_template('staff_dashboard.html')


# ============================================================
#  LOGIN API
# ============================================================

@app.route('/api/login', methods=['POST'])
def api_login():
    data     = request.get_json()
    user_id  = data.get('id', '').strip().upper()
    password = data.get('password', '')
    role     = data.get('role', 'student')

    if not user_id or not password:
        return jsonify({"success": False, "message": "All fields are required."})

    pw_hash = hash_password(password)

    try:
        conn   = get_db_connection()
        cursor = conn.cursor()

        if role == 'student':
            cursor.execute(
                "SELECT student_id, full_name, email, is_active FROM students WHERE student_id = :1 AND password_hash = :2",
                [user_id, pw_hash]
            )
            row = cursor.fetchone()
            if row is None:
                return jsonify({"success": False, "message": "Invalid Student ID or password."})
            student_id, full_name, email, is_active = row
            if not is_active:
                return jsonify({"success": False, "message": "Your account has been deactivated."})
            session.permanent = data.get('remember', False)
            session['user_id']   = student_id
            session['full_name'] = full_name
            session['email']     = email
            session['role']      = 'student'
            return jsonify({"success": True, "message": "Login successful!", "redirect": "/student-dashboard"})

        elif role == 'staff':
            cursor.execute(
                "SELECT employee_id, full_name, email, staff_role, is_active FROM staff WHERE employee_id = :1 AND password_hash = :2",
                [user_id, pw_hash]
            )
            row = cursor.fetchone()
            if row is None:
                return jsonify({"success": False, "message": "Invalid Employee ID or password."})
            emp_id, full_name, email, staff_role, is_active = row
            if not is_active:
                return jsonify({"success": False, "message": "Your staff account is inactive."})
            session.permanent = data.get('remember', False)
            session['user_id']    = emp_id
            session['full_name']  = full_name
            session['email']      = email
            session['role']       = 'staff'
            session['staff_role'] = staff_role
            return jsonify({"success": True, "message": "Login successful!", "redirect": "/staff-dashboard"})

        else:
            return jsonify({"success": False, "message": "Invalid role."})

    except oracledb.DatabaseError as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": "Database error. Please try again later."})
    finally:
        cursor.close()
        conn.close()


# ============================================================
#  STUDENT API ROUTES
# ============================================================

@app.route('/api/student/me')
@login_required
def api_student_me():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT student_id, full_name, email, department FROM students WHERE student_id = :1",
            [session['user_id']]
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "message": "Student not found."})
        return jsonify({"success": True, "data": {"student_id": row[0], "full_name": row[1], "email": row[2], "department": row[3]}})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/student/issued-books')
@login_required
def api_student_issued_books():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.title, b.author, i.issue_date, i.due_date, i.return_date, i.status
            FROM book_issues i
            JOIN books b ON i.book_id = b.book_id
            WHERE i.student_id = :1 AND i.return_date IS NULL
            ORDER BY i.issue_date DESC
        """, [session['user_id']])
        rows = cursor.fetchall()
        data = [{"title": r[0], "author": r[1], "issue_date": str(r[2]), "due_date": str(r[3]), "return_date": str(r[4]) if r[4] else None, "status": r[5]} for r in rows]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/student/all-books')
@login_required
def api_student_all_books():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.title, b.author, i.issue_date, i.due_date, i.return_date, i.status
            FROM book_issues i
            JOIN books b ON i.book_id = b.book_id
            WHERE i.student_id = :1
            ORDER BY i.issue_date DESC
        """, [session['user_id']])
        rows = cursor.fetchall()
        data = [{"title": r[0], "author": r[1], "issue_date": str(r[2]), "due_date": str(r[3]), "return_date": str(r[4]) if r[4] else None, "status": r[5]} for r in rows]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/student/stats')
@login_required
def api_student_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM book_issues WHERE student_id = :1 AND return_date IS NOT NULL",
            [session['user_id']]
        )
        returned = cursor.fetchone()[0]
        cursor.execute("""
            SELECT f.fine_id, b.title, f.fine_amount
            FROM fines f
            JOIN book_issues i ON f.issue_id = i.issue_id
            JOIN books b ON i.book_id = b.book_id
            WHERE f.student_id = :1 AND f.paid = 0
        """, [session['user_id']])
        rows = cursor.fetchall()
        fines = [{"fine_id": r[0], "title": r[1], "amount": float(r[2])} for r in rows]
        total_fine = sum(f['amount'] for f in fines)
        return jsonify({"success": True, "data": {"returned": returned, "total_fine": total_fine, "fines": fines}})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/student/fines')
@login_required
def api_student_fines():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.title, b.author, f.fine_amount, f.paid,
                   GREATEST(TRUNC(SYSDATE) - TRUNC(i.due_date), 0) AS days_overdue
            FROM fines f
            JOIN book_issues i ON f.issue_id = i.issue_id
            JOIN books b ON i.book_id = b.book_id
            WHERE f.student_id = :1
            ORDER BY f.paid, f.fine_amount DESC
        """, [session['user_id']])
        rows = cursor.fetchall()
        data = [{"title": r[0], "author": r[1], "fine_amount": float(r[2]), "paid": bool(r[3]), "days_overdue": int(r[4])} for r in rows]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/student/reservations')
@login_required
def api_student_reservations():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.reservation_id, b.title, b.author, r.reserved_date, r.status
            FROM reservations r
            JOIN books b ON r.book_id = b.book_id
            WHERE r.student_id = :1 AND r.status = 'pending'
            ORDER BY r.reserved_date DESC
        """, [session['user_id']])
        rows = cursor.fetchall()
        data = [{"reservation_id": r[0], "title": r[1], "author": r[2], "reserved_date": str(r[3]), "status": r[4]} for r in rows]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/student/reservations/<int:res_id>/cancel', methods=['POST'])
@login_required
def api_cancel_reservation(res_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE reservations SET status = 'cancelled' WHERE reservation_id = :1 AND student_id = :2",
            [res_id, session['user_id']]
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()


# ============================================================
#  BOOKS API
# ============================================================

@app.route('/api/books')
@login_required
def api_all_books():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT book_id, isbn, title, author, genre, publisher, publish_year, total_copies, available_copies FROM books ORDER BY title")
        rows = cursor.fetchall()
        data = [{"book_id": r[0], "isbn": r[1], "title": r[2], "author": r[3], "genre": r[4], "publisher": r[5], "publish_year": r[6], "total_copies": r[7], "available_copies": r[8]} for r in rows]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/books/search')
@login_required
def api_search_books():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({"success": False, "message": "No query provided."})
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        like = '%' + q.upper() + '%'
        cursor.execute("""
            SELECT book_id, isbn, title, author, genre, publisher, total_copies, available_copies
            FROM books
            WHERE UPPER(title) LIKE :1 OR UPPER(author) LIKE :1 OR UPPER(isbn) LIKE :1 OR UPPER(genre) LIKE :1
            ORDER BY title
            FETCH FIRST 20 ROWS ONLY
        """, [like])
        rows = cursor.fetchall()
        data = [{"book_id": r[0], "isbn": r[1], "title": r[2], "author": r[3], "genre": r[4], "publisher": r[5], "total_copies": r[6], "available_copies": r[7]} for r in rows]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()


# ============================================================
#  STAFF API ROUTES
# ============================================================

@app.route('/api/staff/me')
@staff_required
def api_staff_me():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT employee_id, full_name, email, staff_role FROM staff WHERE employee_id = :1",
            [session['user_id']]
        )
        row = cursor.fetchone()
        return jsonify({"success": True, "data": {"employee_id": row[0], "full_name": row[1], "email": row[2], "staff_role": row[3]}})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/staff/dashboard-stats')
@staff_required
def api_staff_dashboard_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM books")
        total_books = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM book_issues WHERE return_date IS NULL AND due_date < SYSDATE")
        overdue = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM students WHERE is_active = 1")
        members = cursor.fetchone()[0]
        cursor.execute("SELECT NVL(SUM(fine_amount), 0) FROM fines WHERE paid = 0")
        fines = float(cursor.fetchone()[0])
        return jsonify({"success": True, "data": {"total_books": total_books, "overdue_count": overdue, "active_members": members, "unpaid_fines": fines}})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/staff/recent-issues')
@staff_required
def api_staff_recent_issues():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.title, b.author, s.full_name, i.student_id, i.issue_date, i.due_date, i.return_date
            FROM book_issues i
            JOIN books b ON i.book_id = b.book_id
            JOIN students s ON i.student_id = s.student_id
            ORDER BY i.issue_date DESC
            FETCH FIRST 10 ROWS ONLY
        """)
        rows = cursor.fetchall()
        data = [{"title": r[0], "author": r[1], "student_name": r[2], "student_id": r[3], "issue_date": str(r[4]), "due_date": str(r[5]), "return_date": str(r[6]) if r[6] else None} for r in rows]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/staff/overdue')
@staff_required
def api_staff_overdue():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.full_name, i.student_id, b.title, TRUNC(SYSDATE - i.due_date) AS days_overdue
            FROM book_issues i
            JOIN books b ON i.book_id = b.book_id
            JOIN students s ON i.student_id = s.student_id
            WHERE i.return_date IS NULL AND i.due_date < SYSDATE
            ORDER BY days_overdue DESC
            FETCH FIRST 10 ROWS ONLY
        """)
        rows = cursor.fetchall()
        data = [{"student_name": r[0], "student_id": r[1], "title": r[2], "days_overdue": int(r[3])} for r in rows]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/staff/books', methods=['POST'])
@staff_required
def api_add_book():
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        copies = int(data.get('total_copies', 1))
        cursor.execute("""
            INSERT INTO books (isbn, title, author, genre, publisher, publish_year, total_copies, available_copies, added_by)
            VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9)
        """, [data['isbn'], data['title'], data['author'], data.get('genre'), data.get('publisher'), data.get('publish_year'), copies, copies, session['user_id']])
        conn.commit()
        return jsonify({"success": True, "message": "Book added."})
    except oracledb.IntegrityError:
        return jsonify({"success": False, "message": "A book with this ISBN already exists."})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/staff/books/<int:book_id>', methods=['DELETE'])
@staff_required
def api_delete_book(book_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM books WHERE book_id = :1", [book_id])
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/staff/members')
@staff_required
def api_get_members():
    q = request.args.get('q', '').strip()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if q:
            like = '%' + q.upper() + '%'
            cursor.execute("""
                SELECT s.student_id, s.full_name, s.email, s.department, s.is_active,
                       COUNT(i.issue_id) AS books_issued,
                       NVL(SUM(CASE WHEN f.paid = 0 THEN f.fine_amount ELSE 0 END), 0) AS fine_due
                FROM students s
                LEFT JOIN book_issues i ON s.student_id = i.student_id
                LEFT JOIN fines f ON s.student_id = f.student_id
                WHERE UPPER(s.full_name) LIKE :1 OR UPPER(s.student_id) LIKE :1
                GROUP BY s.student_id, s.full_name, s.email, s.department, s.is_active
                ORDER BY s.full_name
            """, [like])
        else:
            cursor.execute("""
                SELECT s.student_id, s.full_name, s.email, s.department, s.is_active,
                       COUNT(i.issue_id) AS books_issued,
                       NVL(SUM(CASE WHEN f.paid = 0 THEN f.fine_amount ELSE 0 END), 0) AS fine_due
                FROM students s
                LEFT JOIN book_issues i ON s.student_id = i.student_id
                LEFT JOIN fines f ON s.student_id = f.student_id
                GROUP BY s.student_id, s.full_name, s.email, s.department, s.is_active
                ORDER BY s.full_name
            """)
        rows = cursor.fetchall()
        data = [{"student_id": r[0], "full_name": r[1], "email": r[2], "department": r[3], "is_active": bool(r[4]), "books_issued": int(r[5]), "fine_due": float(r[6])} for r in rows]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/staff/members', methods=['POST'])
@staff_required
def api_add_member():
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        pw_hash = hash_password(data['password'])
        cursor.execute("""
            INSERT INTO students (student_id, full_name, email, phone, department, password_hash)
            VALUES (:1, :2, :3, :4, :5, :6)
        """, [data['student_id'], data['full_name'], data['email'], data.get('phone'), data.get('department'), pw_hash])
        conn.commit()
        return jsonify({"success": True})
    except oracledb.IntegrityError:
        return jsonify({"success": False, "message": "Student ID or email already exists."})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/staff/members/<student_id>/toggle', methods=['POST'])
@staff_required
def api_toggle_member(student_id):
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE students SET is_active = :1 WHERE student_id = :2",
            [int(data['is_active']), student_id]
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/staff/issue', methods=['POST'])
@staff_required
def api_issue_book():
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT available_copies FROM books WHERE book_id = :1", [data['book_id']])
        row = cursor.fetchone()
        if not row or row[0] < 1:
            return jsonify({"success": False, "message": "Book is not available."})
        cursor.execute("""
            INSERT INTO book_issues (book_id, student_id, issued_by, due_date)
            VALUES (:1, :2, :3, TO_DATE(:4, 'YYYY-MM-DD'))
        """, [data['book_id'], data['student_id'], session['user_id'], data['due_date']])
        cursor.execute(
            "UPDATE books SET available_copies = available_copies - 1 WHERE book_id = :1",
            [data['book_id']]
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/staff/student-issued/<student_id>')
@staff_required
def api_student_issued_for_return(student_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.issue_id, b.title, b.author, i.due_date
            FROM book_issues i
            JOIN books b ON i.book_id = b.book_id
            WHERE i.student_id = :1 AND i.return_date IS NULL
            ORDER BY i.issue_date DESC
        """, [student_id])
        rows = cursor.fetchall()
        data = [{"issue_id": r[0], "title": r[1], "author": r[2], "due_date": str(r[3])} for r in rows]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/staff/return/<int:issue_id>', methods=['POST'])
@staff_required
def api_return_book(issue_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT book_id, student_id, due_date FROM book_issues WHERE issue_id = :1 AND return_date IS NULL",
            [issue_id]
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "message": "Issue record not found."})
        book_id, student_id, due_date = row
        cursor.execute(
            "UPDATE book_issues SET return_date = SYSDATE, status = 'returned' WHERE issue_id = :1",
            [issue_id]
        )
        cursor.execute(
            "UPDATE books SET available_copies = available_copies + 1 WHERE book_id = :1",
            [book_id]
        )
        cursor.execute("SELECT GREATEST(TRUNC(SYSDATE) - TRUNC(:1), 0) FROM dual", [due_date])
        days_late = int(cursor.fetchone()[0])
        fine_amount = days_late * 2
        if fine_amount > 0:
            cursor.execute(
                "INSERT INTO fines (issue_id, student_id, fine_amount) VALUES (:1, :2, :3)",
                [issue_id, student_id, fine_amount]
            )
        conn.commit()
        return jsonify({"success": True, "fine": fine_amount})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/staff/fines')
@staff_required
def api_staff_fines():
    q = request.args.get('q', '').strip()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if q:
            like = '%' + q.upper() + '%'
            cursor.execute("""
                SELECT f.fine_id, s.full_name, s.student_id, b.title, f.fine_amount, f.paid
                FROM fines f
                JOIN students s ON f.student_id = s.student_id
                JOIN book_issues i ON f.issue_id = i.issue_id
                JOIN books b ON i.book_id = b.book_id
                WHERE UPPER(s.full_name) LIKE :1 OR UPPER(s.student_id) LIKE :1
                ORDER BY f.paid, f.fine_amount DESC
            """, [like])
        else:
            cursor.execute("""
                SELECT f.fine_id, s.full_name, s.student_id, b.title, f.fine_amount, f.paid
                FROM fines f
                JOIN students s ON f.student_id = s.student_id
                JOIN book_issues i ON f.issue_id = i.issue_id
                JOIN books b ON i.book_id = b.book_id
                ORDER BY f.paid, f.fine_amount DESC
            """)
        rows = cursor.fetchall()
        data = [{"fine_id": r[0], "student_name": r[1], "student_id": r[2], "title": r[3], "fine_amount": float(r[4]), "paid": bool(r[5])} for r in rows]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/staff/fines/<int:fine_id>/pay', methods=['POST'])
@staff_required
def api_mark_fine_paid(fine_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE fines SET paid = 1, paid_date = SYSDATE WHERE fine_id = :1", [fine_id])
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/staff/reports')
@staff_required
def api_staff_reports():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.title, COUNT(i.issue_id) AS cnt
            FROM book_issues i JOIN books b ON i.book_id = b.book_id
            GROUP BY b.title ORDER BY cnt DESC FETCH FIRST 5 ROWS ONLY
        """)
        top_books = [{"title": r[0], "issue_count": r[1]} for r in cursor.fetchall()]
        cursor.execute("""
            SELECT s.full_name, COUNT(i.issue_id) AS cnt
            FROM book_issues i JOIN students s ON i.student_id = s.student_id
            GROUP BY s.full_name ORDER BY cnt DESC FETCH FIRST 5 ROWS ONLY
        """)
        top_borrowers = [{"full_name": r[0], "issue_count": r[1]} for r in cursor.fetchall()]
        cursor.execute("""
            SELECT NVL(SUM(fine_amount), 0),
                   NVL(SUM(CASE WHEN paid = 1 THEN fine_amount END), 0),
                   NVL(SUM(CASE WHEN paid = 0 THEN fine_amount END), 0)
            FROM fines
        """)
        fr = cursor.fetchone()
        fines_summary = {"total": float(fr[0]), "paid": float(fr[1]), "unpaid": float(fr[2])}
        return jsonify({"success": True, "data": {"top_books": top_books, "top_borrowers": top_borrowers, "fines_summary": fines_summary}})
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()
        conn.close()

# ============================================================
#  PUBLIC STATS API (no login required — used by login page)
# ============================================================

@app.route('/api/public/stats')
def api_public_stats():
    try:
        conn   = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM books")
        total_books = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM students WHERE is_active = 1")
        total_members = cursor.fetchone()[0]
        cursor.execute("""
            SELECT COUNT(*) FROM book_issues
            WHERE return_date IS NOT NULL
        """)
        total_returns = cursor.fetchone()[0]
        # Calculate return rate
        cursor.execute("SELECT COUNT(*) FROM book_issues")
        total_issues = cursor.fetchone()[0]
        if total_issues > 0:
            return_rate = round((total_returns / total_issues) * 100)
        else:
            return_rate = 98
        return jsonify({
            "success": True,
            "books":       f"{total_books:,}",
            "members":     f"{total_members:,}",
            "return_rate": f"{return_rate}%"
        })
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"success": False, "books": "12,400", "members": "3,200", "return_rate": "98%"})
    finally:
        cursor.close()
        conn.close()

# ============================================================
#  RUN
# ============================================================
if __name__ == '__main__':
    app.run(debug=True, port=5000)
