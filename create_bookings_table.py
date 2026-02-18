import sqlite3

connection = sqlite3.connect("database.db")
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    purpose TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    destination TEXT,
    owner TEXT,
    time_out TEXT NOT NULL,
    return_mileage INTEGER,
    condition TEXT,
    issues TEXT,
    notes TEXT,
    time_in TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
)
""")

connection.commit()
connection.close()

print("Bookings table created.")
