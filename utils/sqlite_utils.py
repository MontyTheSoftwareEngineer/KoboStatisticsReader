import sqlite3

def connect_to_database(temp_file_path):
    try:
        conn = sqlite3.connect(temp_file_path)
        return conn
    except sqlite3.Error as e:
        raise Exception(f"Database connection error: {e}")
