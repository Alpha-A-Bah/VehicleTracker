import sqlite3

# Connect to your existing database
connection = sqlite3.connect("database.db")
cursor = connection.cursor()

# Create the logbook_entries table
cursor.execute("""
CREATE TABLE IF NOT EXISTS logbook_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    booking_id INTEGER NOT NULL,
    user TEXT NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    start_mileage INTEGER NOT NULL,
    end_mileage INTEGER NOT NULL,
    start_postcode TEXT NOT NULL,
    end_postcode TEXT NOT NULL,
    taken_home INTEGER DEFAULT 0,
    home_reason TEXT,
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(id),
    FOREIGN KEY(booking_id) REFERENCES bookings(id)
);
""")

connection.commit()
connection.close()

print("Logbook table created successfully.")
