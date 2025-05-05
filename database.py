import mysql.connector
from config import DB_CONFIG

def create_database():
    conn = mysql.connector.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password']
    )
    cursor = conn.cursor()
    
    # Create database if not exists
    cursor.execute("CREATE DATABASE IF NOT EXISTS attendance_system")
    cursor.execute("USE attendance_system")
    
    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id INT AUTO_INCREMENT PRIMARY KEY,
        student_name VARCHAR(100) NOT NULL,
        roll_number VARCHAR(20) UNIQUE NOT NULL,
        email VARCHAR(100) NOT NULL,
        class VARCHAR(50) NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        attendance_id INT AUTO_INCREMENT PRIMARY KEY,
        student_id INT NOT NULL,
        date DATE NOT NULL,
        status ENUM('Present', 'Absent') NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(student_id),
        UNIQUE KEY unique_attendance (student_id, date)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        teacher_id INT AUTO_INCREMENT PRIMARY KEY,
        teacher_name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL
    )
    """)
    
    # Insert sample data
    try:
        cursor.execute("""
        INSERT INTO students (student_name, roll_number, email, class)
        VALUES 
            ('John Doe', 'S001', 'john@example.com', 'Class 10'),
            ('Jane Smith', 'S002', 'jane@example.com', 'Class 10'),
            ('Mike Johnson', 'S003', 'mike@example.com', 'Class 11')
        """)
        
        cursor.execute("""
        INSERT INTO attendance (student_id, date, status)
        VALUES 
            (1, CURDATE(), 'Present'),
            (2, CURDATE(), 'Present'),
            (3, CURDATE(), 'Absent'),
            (1, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'Present'),
            (2, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'Absent'),
            (3, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'Present')
        """)
        
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Sample data already exists: {err}")
    
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    create_database()
    print("Database setup completed successfully!")