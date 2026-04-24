import sqlite3

def create_users_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            role TEXT DEFAULT 'user'
        )
    """)

def create_vehicles_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registration TEXT UNIQUE NOT NULL,
            make TEXT,
            model TEXT,
            colour TEXT,
            mileage INTEGER,
            status TEXT DEFAULT 'available'
        )
    """)

def create_jobcards_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER,
            user_id INTEGER,
            description TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            FOREIGN KEY(vehicle_id) REFERENCES vehicles(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

def create_notes_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jobcard_id INTEGER,
            user_id INTEGER,
            note TEXT,
            created_at TEXT,
            FOREIGN KEY(jobcard_id) REFERENCES jobcards(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

def create_status_history_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jobcard_id INTEGER,
            old_status TEXT,
            new_status TEXT,
            changed_at TEXT,
            changed_by INTEGER,
            FOREIGN KEY(jobcard_id) REFERENCES jobcards(id),
            FOREIGN KEY(changed_by) REFERENCES users(id)
        )
    """)

def create_all_tables():
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    create_users_table(cursor)
    create_vehicles_table(cursor)
    create_jobcards_table(cursor)
    create_notes_table(cursor)
    create_status_history_table(cursor)

    connection.commit()
    connection.close()

if __name__ == "__main__":
    create_all_tables()
    print("Database tables created successfully.")
