from flask import Flask, render_template, request, redirect, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/vehicles")
def vehicles():
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM vehicles;")
    rows = cursor.fetchall()

    connection.close()
    return render_template("vehicles.html", vehicles=rows)

@app.route("/add_vehicle", methods=["POST"])
def add_vehicle():
    reg = request.form["reg"]
    vin = request.form["vin"]
    model = request.form["model"]
    status = request.form["status"]
    mileage = request.form["mileage"]

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO vehicles (reg, vin, model, status, current_user, current_mileage, last_checkin, last_checkout)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (reg, vin, model, status, None, mileage, None, None))

    connection.commit()
    connection.close()

    flash("Vehicle added successfully!")
    return redirect("/vehicles")

@app.route("/delete_vehicle/<int:vehicle_id>", methods=["POST"])
def delete_vehicle(vehicle_id):
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
    connection.commit()
    connection.close()

    flash("Vehicle deleted.", "warning")
    return redirect("/vehicles")

@app.route("/edit_vehicle/<int:vehicle_id>", methods=["POST"])
def edit_vehicle(vehicle_id):
    reg = request.form["reg"].upper()
    vin = request.form["vin"]
    model = request.form["model"]
    status = request.form["status"]
    mileage = request.form["mileage"]
    owner = request.form["owner"]

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE vehicles
        SET reg = ?, vin = ?, model = ?, status = ?, current_mileage = ?, owner = ?
        WHERE id = ?
    """, (reg, vin, model, status, mileage, owner, vehicle_id))

    connection.commit()
    connection.close()

    flash("Vehicle updated successfully!", "success")
    return redirect("/vehicles")

@app.route("/")
def booking_page():
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    # Available vehicles
    cursor.execute("SELECT * FROM vehicles WHERE status = 'Available'")
    available = cursor.fetchall()

    cursor.execute("""
    SELECT 
        bookings.id AS booking_id,
        vehicles.id AS vehicle_id,
        vehicles.reg,
        vehicles.model,
        bookings.name,
        bookings.time_out
    FROM bookings
    JOIN vehicles ON vehicles.id = bookings.vehicle_id
    WHERE vehicles.status = 'Booked Out' AND bookings.time_in IS NULL
    """)
    active_bookings = cursor.fetchall()



    connection.close()

    return render_template("home.html",
                           available=available,
                           active_bookings=active_bookings)

@app.route("/checkout_vehicle/<int:vehicle_id>", methods=["POST"])
def checkout_vehicle(vehicle_id):
    name = request.form["name"]
    purpose = request.form["purpose"]
    start_time = request.form["start_time"]
    end_time = request.form["end_time"]
    owner = request.form["owner"]
    destination = request.form.get("destination", "")

    time_out = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    connection = sqlite3.connect("database.db", timeout=5)
    cursor = connection.cursor()

    # Insert booking record
    cursor.execute("""
        INSERT INTO bookings (vehicle_id, name, purpose, start_time, end_time, destination, owner, time_out)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (vehicle_id, name, purpose, start_time, end_time, destination, owner, time_out))

    # Update vehicle status
    cursor.execute("""
        UPDATE vehicles
        SET status = 'Booked Out', current_user = ?
        WHERE id = ?
    """, (name, vehicle_id))

    connection.commit()
    connection.close()

    flash("Vehicle checked out successfully!", "success")
    return redirect("/")


@app.route("/checkin_vehicle/<int:booking_id>", methods=["POST"])
def checkin_vehicle(booking_id):
    return_mileage = request.form["return_mileage"]
    condition = request.form["condition"]
    issues = request.form.get("issues", "")
    notes = request.form.get("notes", "")
    time_in = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    connection = sqlite3.connect("database.db", timeout=5)
    cursor = connection.cursor()

    # Update booking record
    cursor.execute("""
        UPDATE bookings
        SET return_mileage = ?, condition = ?, issues = ?, notes = ?, time_in = ?, status = 'completed'
        WHERE id = ?
    """, (return_mileage, condition, issues, notes, time_in, booking_id))

    # Get vehicle ID from booking
    cursor.execute("SELECT vehicle_id FROM bookings WHERE id = ?", (booking_id,))
    vehicle_id = cursor.fetchone()[0]

    # Update vehicle mileage + status
    cursor.execute("""
        UPDATE vehicles
        SET current_mileage = ?, status = 'Available', current_user = NULL
        WHERE id = ?
    """, (return_mileage, vehicle_id))

    connection.commit()
    connection.close()

    flash("Vehicle checked in successfully!", "success")
    return redirect("/")

@app.route("/bookings")
def bookings():
    connection = sqlite3.connect("database.db", timeout=10)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, vehicle_id, name, purpose, start_time, end_time,
               time_out, time_in, return_mileage, status
        FROM bookings
        ORDER BY time_out DESC
    """)

    all_bookings = cursor.fetchall()
    connection.close()

    return render_template("bookings.html", bookings=all_bookings)







if __name__ == "__main__":
    app.run(debug=True, port=5000)
