import oracledb
import hashlib

conn = oracledb.connect(user='system', password='database', dsn='localhost:1521/XE')
cursor = conn.cursor()
pw = hashlib.sha256('password123'.encode()).hexdigest()
print('Hash:', pw)
cursor.execute(
    'SELECT student_id, full_name FROM students WHERE student_id = :1 AND password_hash = :2',
    ['STU2024001', pw]
)
row = cursor.fetchone()
print('Row:', row)
conn.close()
print('Done!')
