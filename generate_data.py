# ============================================================
#  LibraX – Bulk Data Generator
#  Generates 12,400 books and 3,200 students
#  File: generate_data.py  (place in librax/ folder)
#  Run: python generate_data.py
# ============================================================

import oracledb
import hashlib
import random

# ── DB CONFIG (same as app.py) ──
DB_CONFIG = {
    "user":     "system",
    "password": "database",
    "dsn":      "localhost:1521/XE",
}

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

PW_HASH = hash_password("password123")

# ── DATA POOLS ──
FIRST_NAMES = [
    "Aarav","Aakash","Abhishek","Aditya","Ajay","Akash","Alok","Amit","Anand","Anil",
    "Ankit","Ankur","Anuj","Arjun","Arnav","Aryan","Ashish","Ashok","Atul","Ayaan",
    "Deepak","Dev","Dhruv","Dinesh","Farhan","Gaurav","Girish","Harsh","Hemant","Ishan",
    "Jai","Karan","Karthik","Kunal","Mahesh","Manish","Manoj","Milan","Mohit","Neeraj",
    "Nikhil","Nitin","Om","Pankaj","Pranav","Prashant","Prateek","Praveen","Puneet","Rahul",
    "Raj","Rajesh","Rakesh","Ravi","Ritesh","Rohan","Rohit","Sachin","Sagar","Sahil",
    "Sandeep","Sanjay","Shubham","Siddharth","Sourav","Sudhir","Sunil","Suresh","Tarun","Tushar",
    "Uday","Vaibhav","Vikram","Vikas","Vinay","Vishal","Yash","Yogesh","Zaid","Zubin",
    "Aishwarya","Akanksha","Anjali","Ananya","Archana","Bhavna","Deepika","Divya","Ekta","Garima",
    "Ishita","Jyoti","Kajal","Kavita","Kirti","Komal","Kritika","Lakshmi","Lata","Madhuri",
    "Mansi","Meena","Meera","Monika","Namrata","Neha","Nidhi","Nisha","Poonam","Pooja",
    "Prachi","Pragya","Priya","Radha","Ranjana","Rashmi","Ritu","Rohini","Sakshi","Sangeeta",
    "Sarika","Seema","Shikha","Shweta","Simran","Sneha","Sonal","Sonia","Srishti","Swati",
    "Tanvi","Tanya","Usha","Vandana","Varsha","Vidya","Yamini","Zara","Pallavi","Nandita"
]

LAST_NAMES = [
    "Sharma","Verma","Gupta","Singh","Kumar","Patel","Shah","Mehta","Joshi","Yadav",
    "Chauhan","Mishra","Pandey","Tiwari","Srivastava","Shukla","Dubey","Bose","Das","Roy",
    "Nair","Menon","Pillai","Iyer","Krishnan","Subramaniam","Reddy","Rao","Naidu","Murthy",
    "Hegde","Kamath","Shetty","Pai","Bhat","Rajan","Krishnaswamy","Venkatesh","Balaji","Ramesh",
    "Khan","Ahmed","Ali","Siddiqui","Ansari","Shaikh","Qureshi","Malik","Hussain","Farooqi",
    "George","Thomas","Philip","Mathew","Jacob","Joseph","Varghese","Cherian","Antony","Francis",
    "Desai","Jain","Gandhi","Bhatt","Trivedi","Parekh","Kapoor","Malhotra","Chopra","Khanna",
    "Banerjee","Chatterjee","Mukherjee","Ghosh","Dutta","Sengupta","Chaudhury","Basu","Mitra","Paul"
]

DEPARTMENTS = [
    "Computer Science", "Information Technology", "Electronics",
    "Mechanical Engineering", "Civil Engineering", "Electrical Engineering",
    "Chemical Engineering", "Biotechnology", "Physics", "Mathematics",
    "Business Administration", "Commerce", "Economics", "English Literature", "History"
]

BOOK_TITLES_PREFIX = [
    "Introduction to","Fundamentals of","Advanced","Principles of","Modern","Applied",
    "Essentials of","Understanding","Mastering","Practical","Handbook of","Guide to",
    "Complete","Comprehensive","Elementary","Intermediate","Professional","Expert"
]

BOOK_SUBJECTS = [
    "Data Structures","Algorithms","Database Systems","Operating Systems","Computer Networks",
    "Artificial Intelligence","Machine Learning","Python Programming","Java Programming","Web Development",
    "Software Engineering","Cybersecurity","Cloud Computing","Data Science","Blockchain",
    "Digital Electronics","Circuit Theory","Electromagnetic Theory","Signal Processing","VLSI Design",
    "Thermodynamics","Fluid Mechanics","Strength of Materials","Machine Design","Manufacturing",
    "Structural Analysis","Geotechnical Engineering","Transportation Engineering","Hydraulics","Surveying",
    "Organic Chemistry","Physical Chemistry","Biochemistry","Microbiology","Genetics",
    "Calculus","Linear Algebra","Statistics","Discrete Mathematics","Number Theory",
    "Economics","Accountancy","Business Management","Marketing","Finance",
    "English Grammar","World History","Political Science","Psychology","Sociology",
    "Physics","Quantum Mechanics","Optics","Nuclear Physics","Astrophysics",
    "Environmental Science","Ecology","Zoology","Botany","Geology",
    "Electrical Machines","Power Systems","Control Systems","Instrumentation","Robotics"
]

AUTHORS_FIRST = [
    "Rajesh","Sunil","Amit","Priya","Anita","Deepak","Mahesh","Kavita","Ravi","Sunita",
    "Thomas","James","Robert","Mary","Patricia","Michael","Linda","David","Barbara","William",
    "Richard","Susan","Joseph","Jessica","Charles","Sarah","Christopher","Karen","Daniel","Lisa",
    "Matthew","Nancy","Anthony","Betty","Mark","Sandra","Donald","Ashley","Steven","Dorothy",
    "Paul","Kimberly","Andrew","Emily","Joshua","Donna","Kenneth","Carol","Kevin","Amanda"
]

AUTHORS_LAST = [
    "Sharma","Patel","Kumar","Singh","Verma","Gupta","Joshi","Mishra","Nair","Reddy",
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Wilson","Moore",
    "Taylor","Anderson","Thomas","Jackson","White","Harris","Martin","Thompson","Young","Walker",
    "Hall","Allen","Wright","Scott","Green","Baker","Adams","Nelson","Carter","Mitchell",
    "Roberts","Turner","Phillips","Campbell","Parker","Evans","Edwards","Collins","Stewart","Morris"
]

PUBLISHERS = [
    "Pearson Education","McGraw-Hill","Oxford University Press","Cambridge University Press",
    "Tata McGraw-Hill","Wiley India","Cengage Learning","Springer","Elsevier","PHI Learning",
    "S. Chand Publications","Arihant Publications","Dhanpat Rai","New Age International",
    "Laxmi Publications","BPB Publications","Techmax Publications","Nirali Prakashan",
    "Penguin Books","HarperCollins","Macmillan","Random House","Simon & Schuster"
]

GENRES = [
    "Technology","Computer Science","Engineering","Mathematics","Science",
    "Fiction","Biography","History","Economics","Management",
    "Electronics","Mechanical","Civil","Chemistry","Physics"
]


def generate_books(cursor, count=12400):
    print(f"Inserting {count} books...")
    used_isbns = set()
    inserted = 0
    batch = []

    for i in range(1, count + 1):
        # Generate unique ISBN
        while True:
            isbn = f"978-{random.randint(0,9)}-{random.randint(10000,99999)}-{random.randint(100,999)}-{random.randint(0,9)}"
            if isbn not in used_isbns:
                used_isbns.add(isbn)
                break

        prefix  = random.choice(BOOK_TITLES_PREFIX)
        subject = random.choice(BOOK_SUBJECTS)
        title   = f"{prefix} {subject}"
        author  = f"{random.choice(AUTHORS_FIRST)} {random.choice(AUTHORS_LAST)}"
        genre   = random.choice(GENRES)
        pub     = random.choice(PUBLISHERS)
        year    = random.randint(1990, 2024)
        copies  = random.randint(1, 5)
        staff   = random.choice(['EMP1042','EMP2001','EMP2002','EMP2003'])

        batch.append([isbn, title, author, genre, pub, year, copies, copies, staff])

        if len(batch) == 500:
            cursor.executemany("""
                INSERT INTO books (isbn, title, author, genre, publisher, publish_year, total_copies, available_copies, added_by)
                VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9)
            """, batch)
            inserted += len(batch)
            batch = []
            print(f"  {inserted}/{count} books inserted...")

    if batch:
        cursor.executemany("""
            INSERT INTO books (isbn, title, author, genre, publisher, publish_year, total_copies, available_copies, added_by)
            VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9)
        """, batch)
        inserted += len(batch)

    print(f"✅ {inserted} books inserted!")


def generate_students(cursor, count=3200):
    print(f"Inserting {count} students...")
    used_ids    = set()
    used_emails = set()
    inserted    = 0
    batch       = []
    year_counter = {}

    for i in range(1, count + 1):
        year = random.randint(2020, 2024)
        year_counter[year] = year_counter.get(year, 0) + 1
        num = year_counter[year]

        student_id = f"STU{year}{num:04d}"
        while student_id in used_ids:
            num += 1
            student_id = f"STU{year}{num:04d}"
        used_ids.add(student_id)

        first = random.choice(FIRST_NAMES)
        last  = random.choice(LAST_NAMES)
        name  = f"{first} {last}"

        base_email = f"{first.lower()}.{last.lower()}{random.randint(1,999)}@college.edu"
        while base_email in used_emails:
            base_email = f"{first.lower()}.{last.lower()}{random.randint(1,9999)}@college.edu"
        used_emails.add(base_email)

        phone = f"9{random.randint(100000000, 999999999)}"
        dept  = random.choice(DEPARTMENTS)

        batch.append([student_id, name, base_email, phone, dept, PW_HASH])

        if len(batch) == 500:
            cursor.executemany("""
                INSERT INTO students (student_id, full_name, email, phone, department, password_hash)
                VALUES (:1, :2, :3, :4, :5, :6)
            """, batch)
            inserted += len(batch)
            batch = []
            print(f"  {inserted}/{count} students inserted...")

    if batch:
        cursor.executemany("""
            INSERT INTO students (student_id, full_name, email, phone, department, password_hash)
            VALUES (:1, :2, :3, :4, :5, :6)
        """, batch)
        inserted += len(batch)

    print(f"✅ {inserted} students inserted!")


def main():
    print("Connecting to Oracle...")
    conn   = oracledb.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print("Connected!\n")

    # Check existing counts
    cursor.execute("SELECT COUNT(*) FROM books")
    existing_books = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM students")
    existing_students = cursor.fetchone()[0]

    print(f"Existing books:    {existing_books}")
    print(f"Existing students: {existing_students}\n")

    books_needed    = max(0, 12400 - existing_books)
    students_needed = max(0, 3200  - existing_students)

    if books_needed > 0:
        generate_books(cursor, books_needed)
        conn.commit()
    else:
        print(f"✅ Already have {existing_books} books — no new books needed.")

    if students_needed > 0:
        generate_students(cursor, students_needed)
        conn.commit()
    else:
        print(f"✅ Already have {existing_students} students — no new students needed.")

    # Final counts
    cursor.execute("SELECT COUNT(*) FROM books")
    print(f"\n📚 Total books:    {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM students")
    print(f"👥 Total students: {cursor.fetchone()[0]}")

    cursor.close()
    conn.close()
    print("\n🎉 Done! Your database is fully populated.")

if __name__ == '__main__':
    main()
