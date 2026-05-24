# # import mysql.connector
# # from config import Config

# # class Database:
# #     def __init__(self):
# #         self.host = Config.DB_HOST
# #         self.user = Config.DB_USER
# #         self.password = Config.DB_PASSWORD
# #         self.database = Config.DB_NAME
# #         self.connection = None

# #     def connect(self):
# #         try:
# #             self.connection = mysql.connector.connect(
# #                 host=self.host,
# #                 user=self.user,
# #                 password=self.password,
# #                 database=self.database
# #             )
# #             return self.connection
# #         except mysql.connector.Error as err:
# #             print(f"Error: {err}")
# #             return None

# #     def execute_query(self, query, params=None):
# #         connection = self.connect()
# #         if connection is None:
# #             return None

# #         cursor = connection.cursor(dictionary=True)
# #         try:
# #             if params:
# #                 cursor.execute(query, params)
# #             else:
# #                 cursor.execute(query)

# #             if query.strip().lower().startswith('select'):
# #                 result = cursor.fetchall()
# #             else:
# #                 connection.commit()
# #                 result = cursor.lastrowid

# #             cursor.close()
# #             connection.close()
# #             return result
# #         except mysql.connector.Error as err:
# #             print(f"Error: {err}")
# #             cursor.close()
# #             connection.close()
# #             return None
        
# # def mark_absentees_for_lecture(lecture_id, faculty_id):
# #     db = Database()

# #     # Get all students
# #     students = db.execute_query("SELECT id FROM users")
# #     if not students:
# #         return "No students found."

# #     all_ids = [s['id'] for s in students]

# #     # Get all who are present today for this lecture
# #     present = db.execute_query("""
# #         SELECT student_id FROM attendance
# #         WHERE lecture_id = %s AND faculty_id = %s
# #           AND DATE(attendance_time) = CURDATE()
# #           AND status = 'Present'
# #     """, (lecture_id, faculty_id)) or []
# #     present_ids = [p['student_id'] for p in present]

# #     # Find absentees
# #     absentees = set(all_ids) - set(present_ids)

# #     for sid in absentees:
# #         # Insert Absent into attendance table
# #         db.execute_query("""
# #             INSERT INTO attendance (student_id, lecture_id, faculty_id, status, attendance_time)
# #             VALUES (%s, %s, %s, 'Absent', NOW())
# #         """, (sid, lecture_id, faculty_id))

# #         # Optionally insert into absence_records
# #         db.execute_query("""
# #             INSERT IGNORE INTO absence_records (student_id, lecture_id, faculty_id, absence_date)
# #             VALUES (%s, %s, %s, CURDATE())
# #         """, (sid, lecture_id, faculty_id))

# #     return f"Marked {len(absentees)} absentees for lecture {lecture_id}"

# # def setup_database(self):
# #         # Create database if not exists
# #         conn = mysql.connector.connect(
# #             host=self.host,
# #             user=self.user,
# #             password=self.password
# #         )
# #         cursor = conn.cursor()
# #         cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
# #         cursor.close()
# #         conn.close()

# #         # Connect to the specific database
# #         self.connect()

# #         # Create tables
# #         queries = [
# #             """
# #             CREATE TABLE IF NOT EXISTS users (
# #                 id INT AUTO_INCREMENT PRIMARY KEY,
# #                 student_id VARCHAR(20) UNIQUE NOT NULL,
# #                 name VARCHAR(100) NOT NULL,
# #                 email VARCHAR(100) UNIQUE NOT NULL,
# #                 photo_path VARCHAR(255) NOT NULL,
# #                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# #             )
# #             """,
# #             """
# #             CREATE TABLE IF NOT EXISTS faculty (
# #                 id INT AUTO_INCREMENT PRIMARY KEY,
# #                 faculty_id VARCHAR(20) UNIQUE NOT NULL,
# #                 name VARCHAR(100) NOT NULL,
# #                 email VARCHAR(100) UNIQUE NOT NULL,
# #                 password VARCHAR(255) NOT NULL,
# #                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# #             )
# #             """,
# #             """
# #             CREATE TABLE IF NOT EXISTS lectures (
# #                 id INT AUTO_INCREMENT PRIMARY KEY,
# #                 lecture_code VARCHAR(20) UNIQUE NOT NULL,
# #                 title VARCHAR(100) NOT NULL,
# #                 description TEXT,
# #                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# #             )
# #             """,
# #             """
# #             CREATE TABLE IF NOT EXISTS lecture_faculty (
# #                 id INT AUTO_INCREMENT PRIMARY KEY,
# #                 lecture_id INT NOT NULL,
# #                 faculty_id INT NOT NULL,
# #                 FOREIGN KEY (lecture_id) REFERENCES lectures(id),
# #                 FOREIGN KEY (faculty_id) REFERENCES faculty(id),
# #                 UNIQUE KEY unique_lecture_faculty (lecture_id, faculty_id)
# #             )
# #             """,
# #             """
# #             CREATE TABLE IF NOT EXISTS attendance (
# #                 id INT AUTO_INCREMENT PRIMARY KEY,
# #                 student_id INT NOT NULL,
# #                 lecture_id INT NOT NULL,
# #                 faculty_id INT NOT NULL,
# #                 attendance_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
# #                 status ENUM('Present', 'Absent') DEFAULT 'Present',
# #                 FOREIGN KEY (student_id) REFERENCES users(id),
# #                 FOREIGN KEY (lecture_id) REFERENCES lectures(id),
# #                 FOREIGN KEY (faculty_id) REFERENCES faculty(id)
# #             )
# #             """,
# #             """
# #             CREATE TABLE IF NOT EXISTS absence_records (
# #                 id INT AUTO_INCREMENT PRIMARY KEY,
# #                 student_id INT NOT NULL,
# #                 lecture_id INT NOT NULL,
# #                 faculty_id INT NOT NULL,
# #                 absence_date DATE NOT NULL,
# #                 reason TEXT,
# #                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
# #                 FOREIGN KEY (student_id) REFERENCES users(id),
# #                 FOREIGN KEY (lecture_id) REFERENCES lectures(id),
# #                 FOREIGN KEY (faculty_id) REFERENCES faculty(id),
# #                 UNIQUE KEY unique_absence_record (student_id, lecture_id, absence_date)
# #             )
# #             """
# #         ]

# #         for query in queries:
# #             self.execute_query(query)
# import mysql.connector
# from config import Config

# class Database:
#     def __init__(self):
#         self.host = Config.DB_HOST
#         self.user = Config.DB_USER
#         self.password = Config.DB_PASSWORD
#         self.database = Config.DB_NAME
#         self.connection = None

#     def connect(self):
#         try:
#             self.connection = mysql.connector.connect(
#                 host=self.host,
#                 user=self.user,
#                 password=self.password,
#                 database=self.database
#             )
#             return self.connection
#         except mysql.connector.Error as err:
#             print(f"Error: {err}")
#             return None

#     def execute_query(self, query, params=None):
#         connection = self.connect()
#         if connection is None:
#             return None

#         cursor = connection.cursor(dictionary=True)
#         try:
#             if params:
#                 cursor.execute(query, params)
#             else:
#                 cursor.execute(query)

#             if query.strip().lower().startswith('select'):
#                 result = cursor.fetchall()
#             else:
#                 connection.commit()
#                 result = cursor.lastrowid

#             cursor.close()
#             connection.close()
#             return result
#         except mysql.connector.Error as err:
#             print(f"Error: {err}")
#             cursor.close()
#             connection.close()
#             return None

#     def setup_database(self):
#         # Create database if not exists
#         conn = mysql.connector.connect(
#             host=self.host,
#             user=self.user,
#             password=self.password
#         )
#         cursor = conn.cursor()
#         cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
#         cursor.close()
#         conn.close()

#         # Connect to the specific database
#         self.connect()

#         # Create tables
#         queries = [
#             """
#             CREATE TABLE IF NOT EXISTS users (
#                 id INT AUTO_INCREMENT PRIMARY KEY,
#                 student_id VARCHAR(20) UNIQUE NOT NULL,
#                 name VARCHAR(100) NOT NULL,
#                 email VARCHAR(100) UNIQUE NOT NULL,
#                 photo_path VARCHAR(255) NOT NULL,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#             """,
#             """
#             CREATE TABLE IF NOT EXISTS faculty (
#                 id INT AUTO_INCREMENT PRIMARY KEY,
#                 faculty_id VARCHAR(20) UNIQUE NOT NULL,
#                 name VARCHAR(100) NOT NULL,
#                 email VARCHAR(100) UNIQUE NOT NULL,
#                 password VARCHAR(255) NOT NULL,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#             """,
#             """
#             CREATE TABLE IF NOT EXISTS lectures (
#                 id INT AUTO_INCREMENT PRIMARY KEY,
#                 lecture_code VARCHAR(20) UNIQUE NOT NULL,
#                 title VARCHAR(100) NOT NULL,
#                 description TEXT,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#             """,
#             """
#             CREATE TABLE IF NOT EXISTS lecture_faculty (
#                 id INT AUTO_INCREMENT PRIMARY KEY,
#                 lecture_id INT NOT NULL,
#                 faculty_id INT NOT NULL,
#                 FOREIGN KEY (lecture_id) REFERENCES lectures(id),
#                 FOREIGN KEY (faculty_id) REFERENCES faculty(id),
#                 UNIQUE KEY unique_lecture_faculty (lecture_id, faculty_id)
#             )
#             """,
#             """
#             CREATE TABLE IF NOT EXISTS attendance (
#                 id INT AUTO_INCREMENT PRIMARY KEY,
#                 student_id INT NOT NULL,
#                 lecture_id INT NOT NULL,
#                 faculty_id INT NOT NULL,
#                 attendance_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 status ENUM('Present', 'Absent') DEFAULT 'Present',
#                 FOREIGN KEY (student_id) REFERENCES users(id),
#                 FOREIGN KEY (lecture_id) REFERENCES lectures(id),
#                 FOREIGN KEY (faculty_id) REFERENCES faculty(id)
#             )
#             """,
#             """
#             CREATE TABLE IF NOT EXISTS absence_records (
#                 id INT AUTO_INCREMENT PRIMARY KEY,
#                 student_id INT NOT NULL,
#                 lecture_id INT NOT NULL,
#                 faculty_id INT NOT NULL,
#                 absence_date DATE NOT NULL,
#                 reason TEXT,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 FOREIGN KEY (student_id) REFERENCES users(id),
#                 FOREIGN KEY (lecture_id) REFERENCES lectures(id),
#                 FOREIGN KEY (faculty_id) REFERENCES faculty(id),
#                 UNIQUE KEY unique_absence_record (student_id, lecture_id, absence_date)
#             )
#             """

#             # Add this to your database.py setup_database() method after existing tables
# """
# CREATE TABLE IF NOT EXISTS lecture_students (
#     id INT AUTO_INCREMENT PRIMARY KEY,
#     lecture_id INT NOT NULL,
#     student_id INT NOT NULL,
#     enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#     FOREIGN KEY (lecture_id) REFERENCES lectures(id),
#     FOREIGN KEY (student_id) REFERENCES users(id),
#     UNIQUE KEY unique_lecture_student (lecture_id, student_id)
# )
# """
#         ]

#         for query in queries:
#             self.execute_query(query)

import mysql.connector
from config import Config

class Database:
    def __init__(self):
        self.host = Config.DB_HOST
        self.user = Config.DB_USER
        self.password = Config.DB_PASSWORD
        self.database = Config.DB_NAME
        self.connection = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            return self.connection
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return None

    def execute_query(self, query, params=None):
        connection = self.connect()
        if connection is None:
            return None

        cursor = connection.cursor(dictionary=True)
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if query.strip().lower().startswith('select'):
                result = cursor.fetchall()
            else:
                connection.commit()
                result = cursor.lastrowid

            cursor.close()
            connection.close()
            return result
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            cursor.close()
            connection.close()
            return None

    def setup_database(self):
        # Create database if not exists
        conn = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
        cursor.close()
        conn.close()

        # Connect to the specific database
        self.connect()

        # Create tables - CORRECTED VERSION
        queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(20) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                photo_path VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS faculty (
                id INT AUTO_INCREMENT PRIMARY KEY,
                faculty_id VARCHAR(20) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS lectures (
                id INT AUTO_INCREMENT PRIMARY KEY,
                lecture_code VARCHAR(20) UNIQUE NOT NULL,
                title VARCHAR(100) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS lecture_faculty (
                id INT AUTO_INCREMENT PRIMARY KEY,
                lecture_id INT NOT NULL,
                faculty_id INT NOT NULL,
                FOREIGN KEY (lecture_id) REFERENCES lectures(id),
                FOREIGN KEY (faculty_id) REFERENCES faculty(id),
                UNIQUE KEY unique_lecture_faculty (lecture_id, faculty_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                lecture_id INT NOT NULL,
                faculty_id INT NOT NULL,
                attendance_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status ENUM('Present', 'Absent') DEFAULT 'Present',
                FOREIGN KEY (student_id) REFERENCES users(id),
                FOREIGN KEY (lecture_id) REFERENCES lectures(id),
                FOREIGN KEY (faculty_id) REFERENCES faculty(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS absence_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                lecture_id INT NOT NULL,
                faculty_id INT NOT NULL,
                absence_date DATE NOT NULL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id),
                FOREIGN KEY (lecture_id) REFERENCES lectures(id),
                FOREIGN KEY (faculty_id) REFERENCES faculty(id),
                UNIQUE KEY unique_absence_record (student_id, lecture_id, absence_date)
            )
            """,
            # ✅ CORRECTED: Added lecture_students table properly
            """
            CREATE TABLE IF NOT EXISTS lecture_students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                lecture_id INT NOT NULL,
                student_id INT NOT NULL,
                enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lecture_id) REFERENCES lectures(id),
                FOREIGN KEY (student_id) REFERENCES users(id),
                UNIQUE KEY unique_lecture_student (lecture_id, student_id)
            )
            """
        ]

        for query in queries:
            try:
                self.execute_query(query)
                print(f"✅ Table created successfully")
            except Exception as e:
                print(f"❌ Error creating table: {e}")

def mark_absentees_for_lecture(lecture_id, faculty_id):
    db = Database()

    # Get all students
    students = db.execute_query("SELECT id FROM users")
    if not students:
        return "No students found."

    all_ids = [s['id'] for s in students]

    # Get all who are present today for this lecture
    present = db.execute_query("""
        SELECT student_id FROM attendance
        WHERE lecture_id = %s AND faculty_id = %s
            AND DATE(attendance_time) = CURDATE()
            AND status = 'Present'
    """, (lecture_id, faculty_id)) or []
    present_ids = [p['student_id'] for p in present]

    # Find absentees
    absentees = set(all_ids) - set(present_ids)

    for sid in absentees:
        # Insert Absent into attendance table
        db.execute_query("""
            INSERT INTO attendance (student_id, lecture_id, faculty_id, status, attendance_time)
            VALUES (%s, %s, %s, 'Absent', NOW())
        """, (sid, lecture_id, faculty_id))

        # Optionally insert into absence_records
        db.execute_query("""
            INSERT IGNORE INTO absence_records (student_id, lecture_id, faculty_id, absence_date)
            VALUES (%s, %s, %s, CURDATE())
        """, (sid, lecture_id, faculty_id))

    return f"Marked {len(absentees)} absentees for lecture {lecture_id}"

# Add this function to your database.py
def setup_attendance_sessions():
    """Create attendance_sessions table if not exists"""
    db = Database()
    
    query = """
    CREATE TABLE IF NOT EXISTS attendance_sessions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        lecture_id INT NOT NULL,
        faculty_id INT NOT NULL,
        session_date DATE NOT NULL,
        status ENUM('active', 'ended') DEFAULT 'active',
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ended_at TIMESTAMP NULL,
        total_students INT DEFAULT 0,
        present_count INT DEFAULT 0,
        absent_count INT DEFAULT 0,
        FOREIGN KEY (lecture_id) REFERENCES lectures(id),
        FOREIGN KEY (faculty_id) REFERENCES faculty(id),
        UNIQUE KEY unique_session (lecture_id, faculty_id, session_date)
    )
    """
    db.execute_query(query)
    