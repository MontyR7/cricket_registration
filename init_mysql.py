import mysql.connector
from dotenv import load_dotenv
import os
from werkzeug.security import generate_password_hash

# Load environment variables
load_dotenv()

def init_mysql():
    # MySQL connection configuration
    config = {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }

    try:
        # Connect to MySQL server
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        # Create database if it doesn't exist
        db_name = os.getenv('DB_NAME')
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"Database {db_name} created successfully!")

        # Use the created database
        cursor.execute(f"USE {db_name}")

        # Create admin user if not exists
        admin_username = 'admin'  # Default admin username
        admin_password = 'mark$123'  # Default admin password
        
        # Check if admin table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            )
        """)
        
        # Check if admin user exists
        cursor.execute("SELECT id FROM admin WHERE username = %s", (admin_username,))
        if not cursor.fetchone():
            # Create admin user
            hashed_password = generate_password_hash(admin_password)
            cursor.execute(
                "INSERT INTO admin (username, password) VALUES (%s, %s)",
                (admin_username, hashed_password)
            )
            print(f"Default admin user created with username: {admin_username} and password: {admin_password}")
        
        # Commit changes
        conn.commit()
        print("Database initialization completed successfully!")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        raise

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    init_mysql()