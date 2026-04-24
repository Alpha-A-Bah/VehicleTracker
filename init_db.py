import sqlite3

# CHANGE THIS to your real email if needed
YOUR_EMAIL = "Alpha.Bah@changanuk.com"

def make_admin():
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET role = 'superuser'
        WHERE email = ?
    """, (YOUR_EMAIL,))

    connection.commit()
    connection.close()

    print(f"{YOUR_EMAIL} is now a superuser.")

if __name__ == "__main__":
    make_admin()
