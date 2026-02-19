from flask import Flask, render_template, request, redirect, flash, session
from functools import wraps
from dotenv import load_dotenv
import os
import msal
import sqlite3
from datetime import datetime

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
REDIRECT_PATH = os.getenv("REDIRECT_PATH")
AUTHORITY = os.getenv("AUTHORITY")
SCOPE = [os.getenv("SCOPE")]


print("CLIENT SECRET IN FLASK:", repr(CLIENT_SECRET))

import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"



def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper


@app.route("/vehicles")
@login_required
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
@login_required
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
        bookings.time_out,
        vehicles.current_mileage           
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

    start_time = datetime.fromisoformat(start_time).strftime("%Y-%m-%d %H:%M:%S")
    end_time = datetime.fromisoformat(end_time).strftime("%Y-%m-%d %H:%M:%S")
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
@login_required
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


@app.route("/log_journey/<int:booking_id>", methods=["POST"])
@login_required
def log_journey(booking_id):
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    # Get booking info
    cursor.execute("SELECT vehicle_id, name FROM bookings WHERE id = ?", (booking_id,))
    booking = cursor.fetchone()

    if not booking:
        connection.close()
        return "Booking not found", 404

    vehicle_id, user = booking

    # Form data
    start_mileage = int(request.form["start_mileage"])
    end_mileage = int(request.form["end_mileage"])
    start_postcode = request.form["start_postcode"]
    end_postcode = request.form["end_postcode"]
    taken_home = 1 if "taken_home" in request.form else 0
    home_reason = request.form.get("home_reason", None)

    # Validation
    if end_mileage < start_mileage:
        connection.close()
        return "End mileage cannot be lower than start mileage", 400

    # Insert logbook entry
    cursor.execute("""
        INSERT INTO logbook_entries (
            vehicle_id, booking_id, user, start_mileage, end_mileage,
            start_postcode, end_postcode, taken_home, home_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        vehicle_id, booking_id, user, start_mileage, end_mileage,
        start_postcode, end_postcode, taken_home, home_reason
    ))

    # Update vehicle mileage
    cursor.execute("""
        UPDATE vehicles
        SET current_mileage = ?
        WHERE id = ?
    """, (end_mileage, vehicle_id))

    connection.commit()
    connection.close()

    return redirect("/")


@app.route("/logbook")
@login_required
def logbook_page():
    vehicle_id = request.args.get("vehicle_id")
    print("DEBUG vehicle_id =", vehicle_id)

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    if vehicle_id:
        print("DEBUG: Running FILTERED query")
        cursor.execute("""
            SELECT 
                logbook_entries.date,
                vehicles.reg,
                logbook_entries.user,
                logbook_entries.start_mileage,
                logbook_entries.end_mileage,
                logbook_entries.start_postcode,
                logbook_entries.end_postcode,
                logbook_entries.taken_home,
                logbook_entries.home_reason
            FROM logbook_entries
            JOIN vehicles ON vehicles.id = logbook_entries.vehicle_id
            WHERE vehicles.id = ?
            ORDER BY logbook_entries.date DESC
        """, (vehicle_id,))
    else:
        print("DEBUG: Running FULL query")
        cursor.execute("""
            SELECT 
                logbook_entries.date,
                vehicles.reg,
                logbook_entries.user,
                logbook_entries.start_mileage,
                logbook_entries.end_mileage,
                logbook_entries.start_postcode,
                logbook_entries.end_postcode,
                logbook_entries.taken_home,
                logbook_entries.home_reason
            FROM logbook_entries
            JOIN vehicles ON vehicles.id = logbook_entries.vehicle_id
            ORDER BY logbook_entries.date DESC
        """)

    entries = cursor.fetchall()
    connection.close()

    return render_template("logbook.html", entries=entries)

@app.route("/login")
def login():
    session.clear()
    msal_app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )

    auth_url = msal_app.get_authorization_request_url(
    scopes=SCOPE,
    redirect_uri=request.host_url.rstrip("/") + REDIRECT_PATH
)

    

    return redirect(auth_url)

@app.route(REDIRECT_PATH)
def authorized():
    msal_app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )

    code = request.args.get("code")

    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=SCOPE,
        redirect_uri=request.host_url.rstrip("/") + REDIRECT_PATH
    )

    print("MSAL RESULT:", result)


    if "id_token_claims" in result:
        session["user"] = {
            "name": result["id_token_claims"]["name"],
            "email": result["id_token_claims"]["preferred_username"]
        }
        return redirect("/")

    return "Login failed", 401




@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://login.microsoftonline.com/common/oauth2/v2.0/logout"
        "?post_logout_redirect_uri=http://localhost:5000"
    )


@app.after_request
def add_header(response):
    if 'logo.png' in request.path:
        response.headers['Cache-Control'] = 'public, max-age=31536000'
    return response




if __name__ == "__main__":
    app.run(host="localhost", debug=True, port=5000)
