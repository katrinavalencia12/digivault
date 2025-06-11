from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import os
import datetime
import traceback
import json
import uuid
import shutil
import socket
import re
from PIL import Image
from PIL.ExifTags import TAGS
from sqlalchemy import Text
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from email_validator import validate_email, EmailNotValidError
from itsdangerous import URLSafeTimedSerializer

# Flask app and config
app = Flask(__name__, template_folder='../frontend', static_folder='../frontend')
app.secret_key = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 1000 * 1024 * 1024  # 1 GB upload limit
serializer = URLSafeTimedSerializer(app.secret_key)

# Email config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'digivaultcci@gmail.com'
app.config['MAIL_PASSWORD'] = 'egeu pwxr losu pixz'

# Init
db = SQLAlchemy(app)
mail = Mail(app)
scheduler = BackgroundScheduler()
scheduler.start()

UPLOAD_FOLDER = 'uploads'
TRANSLATIONS = {
    "txt": "<p>%s</p>",
    "pdf": '<embed src="%s" type="application/pdf">',
    "mp3": '<audio controls><source src="%s"></audio>',
    "wav": '<audio controls><source src="%s"></audio>',
    "mp4": '<video controls><source src="%s"></video>',
    "mov": '<video controls><source src="%s"></video>',
    "png": '<img src="%s">',
    "jpg": '<img src="%s">',
    "jpeg": '<img src="%s">',
    "gif": '<img src="%s">',
    "webp": '<img src="%s">',
    "bmp": '<img src="%s">',
    "svg": '<img src="%s">',
    "tiff": '<img src="%s">',
}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    badge_five_capsule = db.Column(db.Boolean, default=False)
    badge_first_capsule = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)

class ScheduledDelivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    file_path = db.Column(Text, nullable=False)
    send_at = db.Column(db.DateTime, nullable=False)

class CapsuleHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    capsule_name = db.Column(db.String(100))
    recipient_email = db.Column(db.String(120))
    timestamp = db.Column(db.String(120))  # When it was scheduled/sent
    status = db.Column(db.String(20))  # 'sent' or 'deleted'

# Create tables
with app.app_context():
    db.create_all()

# Metadata extractor
def extract_metadata(file):
    data = {}
    
    try:
        image = Image.open(file)
        exif_data = image._getexif()

        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if type(value) == str:
                    data[tag] = value
    except:
        pass

    return data

# Website builder for capsule receiving
def build_website(user, capsule, files, messages=None):
    # Establish path to file
    PATH = f"../frontend/capsules/{user}/{capsule}"
    os.makedirs(PATH, exist_ok=True)

    # Copy base file
    shutil.copyfile("template/index.html", f"{PATH}/index.html")

    # IP
    ip = get_local_ip()

    # Open new file
    new_file = open(f"{PATH}/index.html", "a")
    if not new_file:
        print("ERROR: FILE NOT FOUND.")
        return
    
    print(messages)

    # Iterate through files
    for index, file in enumerate(files):
        data = extract_metadata(file) # Metadata
        ext = file.split(".")[-1].lower() # File extension

        html = f"<div data-metadata='{json.dumps(data)}'>{(TRANSLATIONS.get(ext, "<p>Unsupported file type.<br>%s</p>") % f"http://{ip}/{file}")}<p>"
        if messages != None and str(index) in messages and messages[str(index)] != "":
            html += f"{messages[str(index)]}"
        else:
            html += "&nbsp;" 

        html += "</p></div>"

        # Write to file
        try:
            new_file.write(html)
        except:
            new_file.write("<p>Error writing this HTML</p>")

    new_file.write("</div><script src='/static/js/capsule.js'></script></body></html>")
    new_file.close()

    # Return path to website
    return PATH + "/index.html"

# Get current server IP (for linking uploads)
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# Email sending function
def send_scheduled_email(email, file_paths, capsule_name, messages=None, sender_username="digivault_user"):
    with app.app_context():
        try:
            # Attempt to find the user by email (could be None for outside recipients)
            user = User.query.filter_by(email=email).first()
            username = user.username if user else "there"
            user_id = user.id if user else None

            msg = Message(
                "Your DigiVault Time Capsule",
                sender="digivaultcci@gmail.com",
                recipients=[email]
            )
            ip = get_local_ip()

            # Use the sender's username instead of recipient's if user not found
            sender_username = sender_username or "digivault_user"  # fallback if passed None
            link = build_website(sender_username, capsule_name, file_paths, messages)

            # Build styled email with view button
            body_html = f"""
            <body style='margin: 0; text-align: center;'>
                <h1 style='width: 100%; text-align: center; color: white; background-color: #2b2f4d; margin: 0; padding: 10px 0; box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.5); user-select: none;'>DigiVault Time Capsules</h1>
                <p style="margin: 40px;">Hi {username}, your time capsule <b>'{capsule_name}'</b> is ready to view.</p>
                <a href="http://{ip}/{link}" style='background-color: #2b2f4d; border: 1px solid #2b2f4d; padding: 10px 25px; color: white; text-decoration: none; text-transform: uppercase; border-radius: 25px; margin: 40px !important; transition: all 0.3s' onmouseover="this.style.backgroundColor='transparent'; this.style.color='black';" onmouseleave="this.style.backgroundColor='#2b2f4d'; this.style.color='white';">View My Capsule</a>
            </body>
            """

            msg.body = "Your files are ready! (If you cannot see links, please view in HTML email format.)"
            msg.html = body_html

            mail.send(msg)
            print(f"[✓] Sent scheduled email to {email} with files: {file_paths}")

            # Log to capsule history only if user is registered
            if user_id:
                history = CapsuleHistory(
                    user_id=user_id,
                    capsule_name=capsule_name,
                    recipient_email=email,
                    timestamp=str(datetime.datetime.utcnow()),
                    status="sent"
                )
                db.session.add(history)
                db.session.commit()

        except Exception as e:
            print(f"[X] Failed to send email to {email}: {e}")

# Routes
@app.route('/')
def index():
    # Render the homepage for all users
    return render_template('index.html')

@app.route('/setup')
def setup():
    # Ensure user is logged in before accessing setup
    if 'user_id' not in session:
        flash('You need to log in to upload files.', 'error')
        return redirect(url_for('login'))
    # Render the setup page where users upload and schedule capsules
    return render_template('setup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Logs the user in by verifying entered password against stored hashed password
    if 'user_id' in session:
        return redirect(url_for('dashboard'))  # Redirect if already logged in

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Find user by username (password is checked separately)
        user = User.query.filter_by(username=username).first()

        if user:
            if not user.is_verified:
                # Prevent login until email is verified
                flash('Please verify your email before logging in.', 'error')
                return redirect(url_for('login'))

            # If password matches, log the user in
            if check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['username'] = user.username
                session['email'] = user.email
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))

        flash('Invalid username or password.', 'error')  # Login failed

    return render_template('login.html')  # Show login form if GET request

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Handles user signup with password validation and confirmation
    if request.method == 'POST':
        username = request.form.get('username').strip()  # Strip leading/trailing whitespace
        email = request.form.get('email').strip()
        password = request.form.get('password').strip()
        confirm_password = request.form.get('confirm_password').strip()

        # Ensure passwords match
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for('signup'))

        # Validate password strength
        if (len(password) < 8 or
            not any(c.islower() for c in password) or
            not any(c.isupper() for c in password) or
            not any(c.isdigit() for c in password)):
            flash("Password must be at least 8 characters and include an uppercase letter, lowercase letter, and number.", "error")
            return redirect(url_for('signup'))

        # Validate and sanitize email format
        try:
            valid = validate_email(email)
            email = valid.email  # Use normalized email
        except EmailNotValidError:
            flash("Invalid email format. Please enter a valid email.", "error")
            return redirect(url_for('signup'))

        # Validate username pattern
        if not re.match(r"^[A-Za-z0-9_]{3,20}$", username):
            flash("Username must be 3–20 characters long and contain only letters, numbers, or underscores.", "error")
            return redirect(url_for('signup'))

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('signup'))
        elif User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return redirect(url_for('signup'))

        # Hash and save new user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # Email verification token
        token = serializer.dumps(email, salt='email-confirm')
        verify_link = url_for('verify_email', token=token, _external=True)

        # Send verification email with styled HTML button
        msg = Message(
            subject="Verify Your DigiVault Email",
            sender="digivaultcci@gmail.com",
            recipients=[email]
        )

        # HTML button format for verification email
        msg.html = f"""
            <h2>Welcome to DigiVault!</h2>
            <p>Hi {username}, please verify your email address by clicking the button below:</p>
            <a href="{verify_link}" style="
                display: inline-block;
                padding: 12px 20px;
                background-color: #28a745;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
            ">
                Verify Email
            </a>
            <p>If the button doesn’t work, you can also copy and paste this URL into your browser:</p>
            <p>{verify_link}</p>
        """

        mail.send(msg)  # Styled email button is now sent

        flash('Signup successful! Please check your email to verify your account.', 'success')
        return redirect(url_for('login'))  # only on successful signup

    return render_template('signup.html')  # Display signup form

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('You need to log in to access the dashboard.', 'error')
        return redirect(url_for('login'))

    print("Fetching capsules")  # <-- Server log for visibility
    capsules = []  # Will hold all time capsules for this user

    # Loop through all scheduled jobs to find ones that match the user
    for job in scheduler.get_jobs():
        split = job.id.split("_")
        # Only fetch capsules belonging to the current user
        if str(split[0]) == str(session['user_id']):
            run_date = job.trigger.run_date  # <-- this is the scheduled datetime
            file_paths = job.args[1]

            # Make sure file_paths is a list, in case it's serialized as a string
            if isinstance(file_paths, str):
                try:
                    file_paths = json.loads(file_paths)
                except:
                    file_paths = []

            # Append capsule data for rendering in dashboard
            capsules.append({
                "job_id": job.id,                       # Used for deletion
                "name": split[3],                       # Capsule name
                "timestamp": run_date.isoformat(),      # Used for countdown
                "email": split[1],                      # Recipient
                "file_path": file_paths                 # List of files
            })

    user = User.query.get(session['user_id'])  # May return None if DB was reset

    if not user:
        flash("User not found. Please log in again.", "error")
        session.clear()
        return redirect(url_for('login'))


    return render_template(
        'dashboard.html',
        username=session['username'],
        email=session['email'],
        capsules=capsules,
        capsulesUploaded=CapsuleHistory.query.filter_by(user_id=session['user_id']).order_by(CapsuleHistory.id.desc()).count()
    )

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        print("== Upload Request Incoming ==")
        print("FILES:", request.files)
        print("FORM:", request.form)

        if 'user_id' not in session:
            return jsonify({"error": "You need to log in to upload files."}), 401

        if 'files' not in request.files:
            return jsonify({"error": "No files selected."}), 400

        files = request.files.getlist('files')
        total_size = sum(len(f.read()) for f in files)
        if total_size > 1000 * 1024 * 1024:
            return jsonify({"error": "File size exceeds 1 GB limit."}), 400

        name = request.form.get('name')
        date = request.form.get('date')
        time = request.form.get('time')
        recipients_raw = request.form.get('recipients', '')
        messages_raw = request.form.get('messages')

        messages = {}
        if messages_raw:
            try:
                messages = json.loads(messages_raw)
            except Exception as e:
                print(f"[X] Failed to load messages JSON: {e}")

        if not date or not time:
            return jsonify({"error": "Date and time must be provided."}), 400

        try:
            scheduled_datetime = datetime.datetime.fromisoformat(f"{date}T{time}")
        except ValueError:
            return jsonify({"error": "Invalid date/time format."}), 400

        file_paths = []

        # Create a user-specific subdirectory in uploads/
        user_upload_dir = os.path.join(UPLOAD_FOLDER, session['username'])
        os.makedirs(user_upload_dir, exist_ok=True)

        for file in files:
            file.seek(0)
            safe_filename = file.filename.replace(' ', '_')
            full_path = os.path.join(user_upload_dir, safe_filename)
            file.save(full_path)
            file_paths.append(full_path)

        recipient_emails = [session['email']]
        if recipients_raw:
            recipient_emails += [email.strip() for email in recipients_raw.split(',') if email.strip()]

        for email in recipient_emails:
            scheduler.add_job(
                func=send_scheduled_email,
                trigger=DateTrigger(run_date=scheduled_datetime),
                args=[email, file_paths, name, messages, session.get("username")],  # added sender_username
                id=f"{session['user_id']}_{email}_{int(scheduled_datetime.timestamp())}_{name}",
                replace_existing=False
             )

        db.session.commit()
        print(f"[\u2713] Upload and schedule completed for {recipient_emails}")
        return jsonify({"message": "File(s) scheduled for delivery!"})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/logout')
def logout():
    # Clear session and log the user out
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/delete_account', methods=['POST'])
def delete_account():
    # Ensure user is logged in
    if 'user_id' not in session:
        flash('You need to log in to delete your account.', 'error')
        return redirect(url_for('login'))
    # Fetch user and delete if exists
    user = User.query.get(session['user_id'])
    if user:
        db.session.delete(user)
        db.session.commit()
        session.clear()
        flash('Your account has been deleted.', 'success')
    else:
        flash('User not found.', 'error')
    # Return to homepage
    return redirect(url_for('index'))

@app.route('/delete_capsule', methods=['POST'])
def delete_capsule():
    try:
        data = request.get_json()
        job_id = data.get("job_id")

        if not job_id or 'user_id' not in session:
            return jsonify({"error": "Unauthorized or invalid request"}), 403

        job = scheduler.get_job(job_id)
        if job:
            # Extract information before deletion
            split = job.id.split("_")
            user_id = session['user_id']
            recipient_email = split[1]
            capsule_name = split[3]
            timestamp = job.trigger.run_date.isoformat()

            # Remove the job from the scheduler
            scheduler.remove_job(job_id)
            print(f"[✓] Deleted capsule: {job_id}")

            # Log this deletion to the history table
            history = CapsuleHistory(
                user_id=user_id,
                capsule_name=capsule_name,
                recipient_email=recipient_email,
                timestamp=timestamp,
                status="deleted"
            )
            db.session.add(history)
            db.session.commit()

            return jsonify({"message": "Capsule deleted successfully."}), 200
        else:
            return jsonify({"error": "Capsule not found."}), 404

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500  # Test for JSON return

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    # If user submits the form to reset their password
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email')  # Get input from form

        # Look up the user by either username or email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if user:
            try:
                # Generate a secure token tied to the user's email
                token = serializer.dumps(user.email, salt='password-reset-salt')
                reset_url = url_for('reset_password', token=token, _external=True)  # Full URL for email

                # Compose the reset email (HTML hides raw token from view)
                msg = Message(
                    subject="Reset Your DigiVault Password",
                    sender="digivaultcci@gmail.com",
                    recipients=[user.email]
                )

                # HTML version of the reset message with clean clickable link
                msg.html = f"""
                <p>Hello {user.username},</p>

                <p>A password reset was requested for your DigiVault account.</p>

                <p>
                    <a href="{reset_url}" 
                       style="background-color: #4CAF50; color: white; padding: 10px 20px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                       Reset Your Password
                    </a>
                </p>

                <p>If you didn't request this, please ignore this email.</p>

                <p>- DigiVault Team</p>
                """

                # Send the email
                mail.send(msg)
                flash("A password reset link has been sent to your email.", "success")
                return redirect(url_for('login'))

            except Exception as e:
                print(f"[X] Failed to send reset email: {e}")
                flash("There was a problem sending the email. Try again later.", "error")
        else:
            # Show error if no matching user
            flash("No account found with that username or email.", "error")
            return redirect(url_for('forgot_password'))

    # Display form to enter username/email for password reset
    return render_template('forgot_password.html')

@app.route('/history')
def history():
    # Ensure user is logged in
    if 'user_id' not in session:
        flash('Please log in to view your capsule history.', 'error')
        return redirect(url_for('login'))

    # Get history records for this user
    user_id = session['user_id']
    history_entries = CapsuleHistory.query.filter_by(user_id=user_id).order_by(CapsuleHistory.id.desc()).all()

    # Render the history page with data
    return render_template('history.html', history=history_entries)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except Exception:
        flash("The reset link is invalid or has expired.", "error")
        return redirect(url_for('forgot_password'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Invalid reset token or user.", "error")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Password confirmation check
        if new_password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(request.url)

        # Password policy check
        if (len(new_password) < 8 or
            not any(c.islower() for c in new_password) or
            not any(c.isupper() for c in new_password) or
            not any(c.isdigit() for c in new_password)):
            flash("Password must be at least 8 characters and include an uppercase letter, lowercase letter, and number.", "error")
            return redirect(request.url)

        # New password must not match the old one
        if check_password_hash(user.password, new_password):
            flash("You cannot reuse your current password. Please choose a different password.", "error")
            return redirect(request.url)

        # Save new password
        hashed_password = generate_password_hash(new_password)
        user.password = hashed_password
        db.session.commit()

        flash("Your password has been reset. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('reset_password.html')

@app.route('/verify_email/<token>')
def verify_email(token):
    try:
        # Decode the token with the original salt; expires after 1 hour (3600s)
        email = serializer.loads(token, salt='email-confirm', max_age=3600)

        # Look up the user based on the email extracted from the token
        user = User.query.filter_by(email=email).first()

        if user:
            # Mark the user as verified in the database
            user.is_verified = True
            db.session.commit()

            # Let the user know their email is confirmed
            flash('Email verified successfully. Please log in.', 'success')
        else:
            # Edge case: Email not found in database (shouldn’t happen unless tampered)
            flash('Invalid verification link.', 'error')

    except Exception:
        # Catch errors like expired token or malformed data
        flash('Verification link is invalid or has expired.', 'error')
        return redirect(url_for('login'))

    # Render confirmation page if successful
    return render_template('verify_email.html')

@app.errorhandler(404)
def page_not_found(e):
    # Render custom 404 page for any broken routes
    return render_template('404.html'), 404

# Run the app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
