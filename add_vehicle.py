import sqlite3

connection = sqlite3.connect("database.db")
cursor = connection.cursor()

cursor.execute("""
INSERT INTO vehicles (reg, vin, model, status, current_user, current_mileage, last_checkin, last_checkout)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (
    "BX75FZW",              # registration
    "LS6CME0P9SK400053",    # VIN
    "S05",           # model
    "available",            # status
    None,                   # current_user
    3992,                  # current mileage
    None,                   # last_checkin
    None                    # last_checkout
))

connection.commit()
connection.close()

print("Vehicle added.")
