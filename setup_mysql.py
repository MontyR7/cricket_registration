import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_database():
    try:
        # Connect to MySQL server
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', '')
        )

        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            db_name = os.getenv('DB_NAME', 'cricket_tournament')
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            print(f"Database '{db_name}' created successfully.")

            # Switch to the created database
            cursor.execute(f"USE {db_name}")

            # Create tables if needed (Flask-Migrate will handle this)
            print("Database setup completed successfully!")

    except Error as e:
        print(f"Error: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed.")

if __name__ == "__main__":
    create_database()