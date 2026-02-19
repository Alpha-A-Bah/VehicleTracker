import sqlite3

# Connect to the database (creates it if it doesn't exist)
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Create the bookings table
cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    purpose TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    destination TEXT NOT NULL,
    email TEXT NOT NULL,                 -- requester email
    status TEXT NOT NULL DEFAULT 'pending',
    rejection_reason TEXT,
    approval_token TEXT UNIQUE
);
""")

conn.commit()
conn.close()

print("Database initialized successfully.")
