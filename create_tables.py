import sqlite3

def create_users_table():
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            role TEXT DEFAULT 'user'
        )
    """)

    connection.commit()
    connection.close()


def create_all_tables():
    create_users_table()
    # Add more tables here later if needed


if __name__ == "__main__":
    create_all_tables()
    print("Database tables created successfully.")
