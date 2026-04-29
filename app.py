from flask import Flask, render_template, request, redirect, flash, session, url_for, jsonify
from functools import wraps
from dotenv import load_dotenv
import os
import msal
import sqlite3
from datetime import datetime
import secrets
import sqlite3
from datetime import datetime


# Use persistent disk on Render, normal file locally
if os.getenv("RENDER"):
    DB_PATH = "/var/data/database.db"
else:
    DB_PATH = "database.db"



load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
REDIRECT_PATH = os.getenv("REDIRECT_PATH")
AUTHORITY = os.getenv("AUTHORITY")
SCOPE = [os.getenv("SCOPE")]


import requests
from flask import session

import smtplib
from email.mime.text import MIMEText

import sqlite3
from werkzeug.middleware.proxy_fix import ProxyFix



def get_db_connection():
    return sqlite3.connect(DB_PATH)


def ensure_user_exists(email, name):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Check if user already exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()

    if not row:
        # Insert new user with default role 'user'
        cursor.execute(
            "INSERT INTO users (email, name, role) VALUES (?, ?, ?)",
            (email, name, "user")
        )
        connection.commit()

    connection.close()

from flask import session

def load_user_role_into_session(email, name):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("SELECT role, name FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()

    if row:
        role, stored_name = row
        session["role"] = role
        session["email"] = email
        session["name"] = stored_name or name
    else:
        # fallback if something unexpected happens
        session["role"] = "user"
        session["email"] = email
        session["name"] = name

    connection.close()

def require_role(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_role = session.get("role")

            # If user has no role or role not allowed → block
            if user_role not in roles:
                return render_template("unauthorized.html"), 403


            return f(*args, **kwargs)
        return decorated
    return wrapper

# -------------------------------
#  HTML Email Wrapper (ADD THIS)
# -------------------------------
def build_html_email(title, content):
    return f"""
    <html>
    <body style="font-family: Inter, Arial, sans-serif; background:#f7f7f7; padding:20px;">

        <div style="max-width:600px; margin:auto; background:white; padding:25px; 
                    border-radius:10px; border:1px solid #e5e5e5;">

            <h2 style="color:#0d47a1; margin-top:0; margin-bottom:15px;">
                {title}
            </h2>

            <div style="font-size:15px; line-height:1.6; color:#333;">
                {content}
            </div>

            <p style="margin-top:30px; font-size:12px; color:#777;">
                This is an automated message from the Vehicle Tracker system.
            </p>

        </div>

    </body>
    </html>
    """


import os
import requests
from email.mime.text import MIMEText

def send_email_smtp(to_email, subject, body):
    sendgrid_key = os.getenv("SENDGRID_API_KEY")
    sender = os.getenv("SMTP_EMAIL")

    if not sendgrid_key:
        print("ERROR: SENDGRID_API_KEY missing")
        return False

    url = "https://api.sendgrid.com/v3/mail/send"

    payload = {
        "personalizations": [
            {
                "to": [{"email": to_email}],
                "subject": subject
            }
        ],
        "from": {"email": sender},
        "content": [
            {
                "type": "text/html",
                "value": body
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {sendgrid_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print("SendGrid response:", response.status_code, response.text)
        return response.status_code in (200, 202)
    except Exception as e:
        print("SendGrid exception:", e)
        return False







def send_approval_email(to_email, booking_id, token):
    subject = "Vehicle Booking Approval Required"

    content = f"""
    A new vehicle booking requires your approval.<br><br>

    <b>Booking ID:</b> {booking_id}<br><br>

    <a href="http://localhost:5000/approve?token={token}"
       style="display:inline-block; padding:10px 18px; background:#0d47a1; color:white;
              text-decoration:none; border-radius:6px; font-weight:600;">
        Approve / Reject Booking
    </a>
    """

    body = build_html_email(subject, content)

    try:
        send_email_smtp(to_email, subject, body)
    except Exception as e:
        print("EMAIL ERROR in send_approval_email:", e)



def send_requester_notification(to_email, decision, reason):
    subject = f"Your Booking Has Been {decision.capitalize()}"

    # Build the HTML content
    content = f"""
    Your vehicle booking has been <b>{decision}</b>.<br><br>

    <b>Rejection reason (if any):</b><br>
    {reason if reason else "No reason provided."}<br><br>

    If you have questions, please contact your supervisor.
    """

    # Wrap inside the HTML template
    body = build_html_email(subject, content)

    # Send the email
    send_email_smtp(to_email, subject, body)

def notify_technician_jobcard_assigned(jobcard_id, technician_id):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Get jobcard + technician info
    row = cursor.execute("""
        SELECT j.description, v.reg, u.email
        FROM jobcards j
        JOIN vehicles v ON j.vehicle_id = v.id
        JOIN users u ON u.id = ?
        WHERE j.id = ?
    """, (technician_id, jobcard_id)).fetchone()

    connection.close()

    subject = "New Jobcard Assigned to You"

    content = f"""
    A new jobcard has been assigned to you.<br><br>

    <b>Vehicle:</b> {row[1]}<br>
    <b>Description:</b> {row[0]}<br><br>

    Please log in to the Vehicle Tracker system to view and complete the task.
    """

    body = build_html_email(subject, content)
    send_email_smtp(row[2], subject, body)

def notify_supervisor_jobcard_completed(to_email, jobcard_id):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    row = cursor.execute("""
        SELECT j.description, v.reg
        FROM jobcards j
        JOIN vehicles v ON j.vehicle_id = v.id
        WHERE j.id = ?
    """, (jobcard_id,)).fetchone()

    connection.close()

    subject = "Jobcard Completed"

    content = f"""
    A jobcard has been marked as completed.<br><br>

    <b>Vehicle:</b> {row[1]}<br>
    <b>Description:</b> {row[0]}<br><br>

    Please log in to review and close the jobcard.
    """

    body = build_html_email(subject, content)

    # TEMP: send to yourself until supervisor emails exist
    send_email_smtp(to_email, subject, body)


def notify_creator_jobcard_declined(to_email, jobcard_id):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    row = cursor.execute("""
        SELECT j.description, v.reg
        FROM jobcards j
        JOIN vehicles v ON j.vehicle_id = v.id
        WHERE j.id = ?
    """, (jobcard_id,)).fetchone()

    connection.close()

    subject = "Jobcard Declined"

    content = f"""
    A jobcard you created has been declined.<br><br>

    <b>Vehicle:</b> {row[1]}<br>
    <b>Description:</b> {row[0]}<br><br>

    Please review the jobcard and make any required changes.
    """

    body = build_html_email(subject, content)

    send_email_smtp(to_email, subject, body)


import requests
from flask import session




from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key")

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

from create_tables import create_all_tables
from create_tables import create_all_tables
create_all_tables()


create_all_tables()   # ⭐ Ensures DB exists on Railway



def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # ⭐ New login check
        if "email" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated


@app.route("/vehicles")
@login_required
@require_role("manager", "admin", "superuser")
def vehicles():
    connection = sqlite3.connect(DB_PATH)
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
    owner = request.form["owner"]
    owner_email = request.form["owner_email"]

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO vehicles (
            reg, vin, model, status, current_user, current_mileage,
            last_checkin, last_checkout, owner, owner_email
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (reg, vin, model, status, None, mileage, None, None, owner, owner_email))

    connection.commit()
    connection.close()

    flash("Vehicle added successfully!")
    return redirect("/vehicles")


@app.route("/delete_vehicle/<int:vehicle_id>", methods=["POST"])
def delete_vehicle(vehicle_id):
    connection = sqlite3.connect(DB_PATH)
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
    owner_email = request.form["owner_email"]

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE vehicles
        SET reg = ?, vin = ?, model = ?, status = ?, current_mileage = ?, owner = ?, owner_email = ?
        WHERE id = ?
    """, (reg, vin, model, status, mileage, owner, owner_email, vehicle_id))

    connection.commit()
    connection.close()

    flash("Vehicle updated successfully!", "success")
    return redirect("/vehicles")


@app.route("/")
@login_required
def booking_page():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Available vehicles
    cursor.execute("""
    SELECT * FROM vehicles
    WHERE id NOT IN (
        SELECT vehicle_id FROM bookings
        WHERE status IN ('pending', 'approved')
    )
    """)
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
    WHERE bookings.status = 'approved'
    AND bookings.time_in IS NULL
    """)
    active_bookings = cursor.fetchall()


    cursor.execute("""
        SELECT id, name, purpose, start_time, end_time, owner, requester_email
        FROM bookings
        WHERE status = 'pending'
        ORDER BY start_time ASC
    """)
    pending = cursor.fetchall()


    connection.close()

    return render_template("home.html",
                           available=available,
                           active_bookings=active_bookings, pending=pending)

from flask import session

@app.route("/checkout_vehicle/<int:vehicle_id>", methods=["POST"])
@login_required
@require_role("manager", "admin", "superuser")
def checkout_vehicle(vehicle_id):
    name = request.form["name"]
    purpose = request.form["purpose"]
    start_time = request.form["start_time"]
    end_time = request.form["end_time"]
    destination = request.form.get("destination", "")

    # ⭐ SAFELY load Azure user claims
    user_claims = session.get("user")
    if not user_claims:
        flash("Your session expired. Please log in again.", "danger")
        return redirect("/login")

    # ⭐ Extract requester email from Azure claims
    requester_email = (
        user_claims.get("email")
        or user_claims.get("preferred_username")
        or user_claims.get("upn")
    )

    # ⭐ Format timestamps
    start_time = datetime.fromisoformat(start_time).strftime("%Y-%m-%d %H:%M:%S")
    end_time = datetime.fromisoformat(end_time).strftime("%Y-%m-%d %H:%M:%S")
    time_out = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    approval_token = secrets.token_urlsafe(32)

    connection = sqlite3.connect(DB_PATH, timeout=5)
    cursor = connection.cursor()

    # ⭐ Get vehicle owner's email
    cursor.execute("SELECT owner_email FROM vehicles WHERE id = ?", (vehicle_id,))
    row = cursor.fetchone()
    owner_email = row[0] if row else None

    # ⭐ Insert booking
    cursor.execute("""
        INSERT INTO bookings (
            vehicle_id,
            name,
            purpose,
            start_time,
            end_time,
            destination,
            owner,
            time_out,
            status,
            approval_token,
            requester_email
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        vehicle_id,
        name,
        purpose,
        start_time,
        end_time,
        destination,
        owner_email,
        time_out,
        "pending",
        approval_token,
        requester_email
    ))

    booking_id = cursor.lastrowid

    # ⭐ Send approval email
    send_approval_email(
        to_email=owner_email,
        booking_id=booking_id,
        token=approval_token
    )

    connection.commit()
    connection.close()

    flash("Vehicle checked out successfully! Awaiting approval.", "success")
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
@require_role("admin", "superuser")
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
    connection = sqlite3.connect(DB_PATH)
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
@require_role("admin", "superuser")
def logbook_page():
    vehicle_id = request.args.get("vehicle_id")
    print("DEBUG vehicle_id =", vehicle_id)

    connection = sqlite3.connect(DB_PATH)
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

    redirect_uri = os.getenv("REDIRECT_URI")
    print("REDIRECT_URI IN LOGIN:", redirect_uri)

    auth_url = msal_app.get_authorization_request_url(
        scopes=SCOPE if isinstance(SCOPE, list) else SCOPE.split(),
        redirect_uri=redirect_uri,
        prompt="select_account"
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
    redirect_uri = os.getenv("REDIRECT_URI")   # ⭐ Always use production redirect

    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=SCOPE if isinstance(SCOPE, list) else SCOPE.split(),
        redirect_uri=redirect_uri
    )

    # ⭐ Handle login failure
    if "error" in result:
        return "Login failed: " + result.get("error_description", "Unknown error"), 401

    # ⭐ Extract Azure user info
    user_info = result.get("id_token_claims", {})
    email = user_info.get("preferred_username")
    name = user_info.get("name")

    # ⭐ Store Azure claims in session
    session["user"] = user_info

    # ⭐ Ensure user exists in DB
    ensure_user_exists(email, name)

    # ⭐ Load role into session
    load_user_role_into_session(email, name)

    # ⭐ Load user_id into session
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    user_row = cursor.execute(
        "SELECT id FROM users WHERE email = ?", (email,)
    ).fetchone()
    connection.close()

    if user_row:
        session["user_id"] = user_row[0]

    # ⭐ Store access token for sending emails
    session["access_token"] = result["access_token"]

    return redirect("/")




    
def require_role(*roles):
    from functools import wraps
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get("role") not in roles:
                return "Unauthorized", 403
            return f(*args, **kwargs)
        return decorated
    return wrapper




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

@app.route("/approve", methods=["GET", "POST"])
def approve_page():
    token = request.args.get("token")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch booking using the token
    cursor.execute("""
        SELECT id, name, purpose, start_time, end_time, destination, requester_email
        FROM bookings
        WHERE approval_token = ?
    """, (token,))
    booking = cursor.fetchone()

    if not booking:
        conn.close()
        return "Invalid or expired approval link."

    booking_id, name, purpose, start_time, end_time, destination, requester_email = booking

    # Handle Approve / Reject
    if request.method == "POST":
        decision = request.form.get("decision")
        reason = request.form.get("reason", "")

        if decision == "approve":
            cursor.execute("""
                UPDATE bookings
                SET status = 'approved',
                    rejection_reason = NULL,
                    approved_by = ?,
                    approved_at = ?
                WHERE id = ?
            """, (
                session["user"]["email"],                 # approver
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                booking_id
            ))

            conn.commit()
            conn.close()

            # Notify requester
            send_requester_notification(requester_email, "approved", "")
            return redirect(url_for("home"))

        elif decision == "reject":
            cursor.execute("""
                UPDATE bookings
                SET status = 'rejected',
                    rejection_reason = ?,
                    approved_by = ?,
                    approved_at = ?
                WHERE id = ?
            """, (
                reason,
                session["user"]["email"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                booking_id
            ))

            conn.commit()
            conn.close()

            # Notify requester
            send_requester_notification(requester_email, "rejected", reason)
            return redirect(url_for("home"))

    conn.close()

    # Render approval page
    return render_template(
        "approve.html",
        booking_id=booking_id,
        name=name,
        purpose=purpose,
        start_time=start_time,
        end_time=end_time,
        destination=destination,
        token=token
    )




@app.route("/approve/confirm", methods=["POST"])
def approve_confirm():
    token = request.form["token"]
    decision = request.form["decision"]
    rejection_reason = request.form.get("rejection_reason", "")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ⭐ Get requester email from the booking
    cursor.execute("SELECT requester_email FROM bookings WHERE approval_token = ?", (token,))
    row = cursor.fetchone()
    requester_email = row[0] if row else None

    # ⭐ Update booking status + rejection reason
    # ⭐ Update booking status + rejection reason
    if decision == "rejected":
        cursor.execute("""
            UPDATE bookings
            SET status = ?, rejection_reason = ?
            WHERE approval_token = ?
        """, (decision, rejection_reason, token))

    else:
        cursor.execute("""
            UPDATE bookings
            SET status = ?, rejection_reason = NULL
            WHERE approval_token = ?
        """, (decision, token))

        # ⭐ Update vehicle status to Booked Out
        cursor.execute("""
            UPDATE vehicles
            SET status = 'Booked Out'
            WHERE id = (
                SELECT vehicle_id FROM bookings WHERE approval_token = ?
            )
        """, (token,))


    conn.commit()
    conn.close()

    # ⭐ Notify the requester
    if requester_email:
        send_requester_notification(
            to_email=requester_email,
            decision=decision,
            reason=rejection_reason
        )

    return render_template(
        "approval_result.html",
        decision=decision,
        rejection_reason=rejection_reason
    )


@app.route('/booking/<int:booking_id>/notes')
def get_booking_notes(booking_id):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("SELECT notes FROM bookings WHERE id = ?", (booking_id,))
    row = cursor.fetchone()

    connection.close()

    if row:
        return jsonify({"notes": row[0] or ""})
    else:
        return jsonify({"notes": ""}), 404


@app.route("/admin/users")

def manage_users():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("SELECT id, email, name, role FROM users")
    users = cursor.fetchall()

    connection.close()
    return render_template("manage_users.html", users=users)

@app.route("/admin/update_role", methods=["POST"])

def update_role():
    user_id = request.form["user_id"]
    new_role = request.form["role"]

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
    connection.commit()
    connection.close()

    flash("User role updated successfully!", "success")
    return redirect("/admin/users")

@app.route("/calendar")
@login_required
def calendar_view():
    return render_template("calendar.html")


@app.route("/api/bookings")
@login_required
def api_bookings():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT 
            b.id,
            b.name,
            v.reg,
            b.start_time,
            b.end_time,
            b.status
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.id
    """)
    rows = cursor.fetchall()
    connection.close()

    events = []
    for row in rows:
        booking_id = row[0]
        user_name = row[1]
        vehicle_reg = row[2]
        start = row[3]
        end = row[4]
        status = row[5]

        # Fix datetime format (space → T)
        if " " in start:
            start = start.replace(" ", "T")
        if " " in end:
            end = end.replace(" ", "T")

        # Colour coding
        color = "#0d6efd"  # blue
        if status == "active":
            color = "#dc3545"  # red
        elif status == "approved":
            color = "#ffc107"  # yellow
        elif status == "completed":
            color = "#198754"  # green

        events.append({
            "id": booking_id,
            "title": f"{vehicle_reg} — {user_name}",
            "start": start,
            "end": end,
            "color": color,
            "extendedProps":{
                "booking_id": booking_id}
                            })

    return jsonify(events)

@app.route("/jobcards/create", methods=["GET", "POST"])
def create_jobcard():
    # Prevent login loop — check for email, not user_id
    if "email" not in session:
        return redirect("/login")

    user_id = session.get("user_id")

    if request.method == "POST":
        vehicle_id = request.form["vehicle_id"]
        description = request.form["description"]
        available_date = request.form["available_date"]
        required_by = request.form["required_by"]

        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        # Insert jobcard with new date fields + correct initial status
        cursor.execute("""
            INSERT INTO jobcards (
                vehicle_id,
                created_by,
                description,
                status,
                available_date,
                required_by
            )
            VALUES (?, ?, ?, 'pending_supervisor', ?, ?)
        """, (vehicle_id, user_id, description, available_date, required_by))

        jobcard_id = cursor.lastrowid
        connection.commit()
        connection.close()

        # TEMP: until real supervisors exist in V2
        supervisor_email = "alpha.bah@changanuk.com"

        # Notify supervisor that a new jobcard is waiting for review
        notify_supervisor_jobcard_submitted(supervisor_email, jobcard_id)

        flash("Jobcard created and sent to supervisor.", "success")
        return redirect("/jobcards")

    # GET: load vehicles for dropdown
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    vehicles = cursor.execute(
        "SELECT id, reg FROM vehicles ORDER BY reg"
    ).fetchall()
    connection.close()

    return render_template("jobcards_create.html", vehicles=vehicles)



@app.route("/jobcards")
def jobcards_home():
    if "email" not in session:
        return redirect("/login")

    role = session.get("role")
    user_id = session.get("user_id")  # optional

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

# Fetch all technicians (TEMP: fetch all users until roles are added)
    technicians = cursor.execute("""
        SELECT id, name FROM users
    """).fetchall()

    # Supervisor sees ALL jobcards
    if role in ["admin", "superuser"]:
        jobcards = cursor.execute("""
            SELECT j.id, j.vehicle_id, j.description, j.status, j.created_at,
                   u.name AS created_by_name,
                   v.reg AS vehicle_reg
            FROM jobcards j
            JOIN users u ON j.created_by = u.id
            JOIN vehicles v ON j.vehicle_id = v.id
            ORDER BY j.created_at DESC
        """).fetchall()

    # Technician sees only assigned jobs
    elif role == "technician":
        jobcards = cursor.execute("""
            SELECT j.id, j.vehicle_id, j.description, j.status, j.created_at,
                   u.name AS created_by_name,
                   v.reg AS vehicle_reg
            FROM jobcards j
            JOIN users u ON j.created_by = u.id
            JOIN vehicles v ON j.vehicle_id = v.id
            WHERE j.assigned_to = ?
            ORDER BY j.created_at DESC
        """, (user_id,)).fetchall()

    # Normal user sees only their own jobcards
    else:
        jobcards = cursor.execute("""
            SELECT j.id, j.vehicle_id, j.description, j.status, j.created_at,
                   u.name AS created_by_name,
                   v.reg AS vehicle_reg
            FROM jobcards j
            JOIN users u ON j.created_by = u.id
            JOIN vehicles v ON j.vehicle_id = v.id
            WHERE j.created_by = ?
            ORDER BY j.created_at DESC
        """, (user_id,)).fetchall()

    connection.close()

    return render_template("jobcards_home.html", 
                       jobcards=jobcards, 
                       role=role,
                       technicians=technicians)


@app.route("/booking/<int:id>")
def booking_details(id):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    row = cursor.execute("""
        SELECT 
            b.id,
            b.name,
            v.reg,
            b.start_time,
            b.end_time,
            b.status,
            b.notes,
            b.purpose
        FROM bookings b
        JOIN vehicles v ON b.vehicle_id = v.id
        WHERE b.id = ?
    """, (id,)).fetchone()

    connection.close()

    return render_template("booking_details.html", booking=row)



@app.route("/jobcards/<int:id>/approve")
def approve_jobcard(id):
    if "email" not in session:
        return redirect("/login")

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Get creator email BEFORE updating
    creator_email = cursor.execute("""
        SELECT u.email
        FROM jobcards j
        JOIN users u ON j.created_by = u.id
        WHERE j.id = ?
    """, (id,)).fetchone()[0]

    # Update status
    cursor.execute("""
        UPDATE jobcards
        SET status = 'approved'
        WHERE id = ?
    """, (id,))

    connection.commit()
    connection.close()

    # Send email to creator
    notify_creator_jobcard_approved(creator_email, id)

    flash("Jobcard approved.", "success")
    return redirect("/jobcards")



@app.route("/jobcards/<int:id>/decline")
def decline_jobcard(id):
    if "email" not in session:
        return redirect("/login")

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Get creator email BEFORE updating
    creator_email = cursor.execute("""
        SELECT u.email
        FROM jobcards j
        JOIN users u ON j.created_by = u.id
        WHERE j.id = ?
    """, (id,)).fetchone()[0]

    # Update status
    cursor.execute("""
        UPDATE jobcards
        SET status = 'declined'
        WHERE id = ?
    """, (id,))

    connection.commit()
    connection.close()

    # Send email to creator
    notify_creator_jobcard_declined(creator_email, id)

    flash("Jobcard declined.", "danger")
    return redirect("/jobcards")




@app.route("/jobcards/<int:id>/assign", methods=["POST"])
def assign_jobcard(id):
    if session.get("role") not in ["admin", "superuser"]:
        return redirect("/unauthorized")

    technician_id = request.form.get("technician_id")

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE jobcards
        SET assigned_to = ?, status = 'assigned'
        WHERE id = ?
    """, (technician_id, id))

    connection.commit()
    connection.close()

    # ⭐ SEND EMAIL HERE
    notify_technician_jobcard_assigned(id, technician_id)

    flash("Jobcard assigned to technician.", "success")
    return redirect("/jobcards")



@app.route("/jobcards/<int:id>/complete")
def complete_jobcard(id):
    if "email" not in session:
        return redirect("/login")

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # TEMP: until real supervisors exist
    supervisor_email = "alpha.bah@changanuk.com"

    # Update status
    cursor.execute("""
        UPDATE jobcards
        SET status = 'completed'
        WHERE id = ?
    """, (id,))

    connection.commit()
    connection.close()

    # FIX: pass BOTH required arguments
    notify_supervisor_jobcard_completed(supervisor_email, id)

    flash("Jobcard marked as completed.", "success")
    return redirect("/jobcards")




@app.route("/jobcards/<int:id>/close")
def close_jobcard(id):
    if "email" not in session:
        return redirect("/login")

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Get creator email BEFORE updating
    creator_email = cursor.execute("""
        SELECT u.email
        FROM jobcards j
        JOIN users u ON j.created_by = u.id
        WHERE j.id = ?
    """, (id,)).fetchone()[0]

    # Update status
    cursor.execute("""
        UPDATE jobcards
        SET status = 'closed'
        WHERE id = ?
    """, (id,))

    connection.commit()
    connection.close()

    # Send email to creator
    notify_creator_jobcard_closed(creator_email, id)

    flash("Jobcard closed.", "info")
    return redirect("/jobcards")


def notify_creator_jobcard_closed(to_email, jobcard_id):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    row = cursor.execute("""
        SELECT j.description, v.reg
        FROM jobcards j
        JOIN vehicles v ON j.vehicle_id = v.id
        WHERE j.id = ?
    """, (jobcard_id,)).fetchone()

    connection.close()

    subject = "Jobcard Closed"

    content = f"""
    A jobcard you created has been closed.<br><br>

    <b>Vehicle:</b> {row[1]}<br>
    <b>Description:</b> {row[0]}<br><br>

    This jobcard is now fully completed and archived.
    """

    body = build_html_email(subject, content)

    send_email_smtp(to_email, subject, body)

def notify_creator_jobcard_approved(to_email, jobcard_id):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    row = cursor.execute("""
        SELECT j.description, v.reg
        FROM jobcards j
        JOIN vehicles v ON j.vehicle_id = v.id
        WHERE j.id = ?
    """, (jobcard_id,)).fetchone()

    connection.close()

    subject = "Jobcard Approved"

    content = f"""
    A jobcard you created has been approved.<br><br>

    <b>Vehicle:</b> {row[1]}<br>
    <b>Description:</b> {row[0]}<br><br>

    You may now proceed to the next stage or review the approved work.
    """

    body = build_html_email(subject, content)

    send_email_smtp(to_email, subject, body)

def notify_supervisor_jobcard_submitted(to_email, jobcard_id):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    row = cursor.execute("""
        SELECT j.description, v.reg
        FROM jobcards j
        JOIN vehicles v ON j.vehicle_id = v.id
        WHERE j.id = ?
    """, (jobcard_id,)).fetchone()

    connection.close()

    subject = "Jobcard Submitted"

    content = f"""
    A jobcard has been submitted for your review.<br><br>

    <b>Vehicle:</b> {row[1]}<br>
    <b>Description:</b> {row[0]}<br><br>

    Please log in to review and approve the jobcard.
    """

    body = build_html_email(subject, content)

    send_email_smtp(to_email, subject, body)


@app.route("/jobcards/details/<int:jobcard_id>")
def jobcard_details(jobcard_id):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    jc = cursor.execute("""
    SELECT 
        jobcards.id,
        vehicles.reg,
        jobcards.description,
        jobcards.status,
        creator.name AS creator_name,
        jobcards.created_at,
        jobcards.available_date,
        jobcards.required_by,
        tech.name AS technician_name
    FROM jobcards
    JOIN vehicles ON jobcards.vehicle_id = vehicles.id
    JOIN users AS creator ON jobcards.created_by = creator.id
    LEFT JOIN users AS tech ON jobcards.assigned_to = tech.id
    WHERE jobcards.id = ?
""", (jobcard_id,)).fetchone()


    connection.close()

    if not jc:
        return "<p>Jobcard not found.</p>"

    return render_template("jobcard_modal.html", jc=jc)

@app.route("/debug-vehicles")
def debug_vehicles():
    import sqlite3
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    rows = cursor.execute("PRAGMA table_info(vehicles)").fetchall()
    connection.close()
    return str(rows)





if __name__ == "__main__":
    app.run(host="localhost", debug=True, port=5000)
