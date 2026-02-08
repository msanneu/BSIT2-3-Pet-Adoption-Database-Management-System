import os
import re
from datetime import datetime
from uuid import uuid4
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import select

app = Flask(__name__)
app.secret_key = "petadopt_secret_2026_key"

# --- 1. CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:@localhost/pet_adoption" 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

upload_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
os.makedirs(upload_dir, exist_ok=True)
app.config['UPLOAD_FOLDER'] = upload_dir
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}

db = SQLAlchemy(app)

# --- 1. CONFIGURATION (Add after db = SQLAlchemy(app)) ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'thepetadoption@gmail.com' # Replace with your email
app.config['MAIL_PASSWORD'] = 'fyen afdm wiks gxwj'   # Replace with your App Password
app.config['MAIL_DEFAULT_SENDER'] = 'office@petadopt.ph'

mail = Mail(app)


# --- 2. MODELS ---

class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    breed = db.Column(db.String(50))
    photo = db.Column(db.String(200))
    age_category = db.Column(db.String(20))    
    gender = db.Column(db.String(10))          
    size = db.Column(db.String(10))            
    energy_level = db.Column(db.String(20))    
    spayed_neutered = db.Column(db.String(5))  
    vac_status = db.Column(db.String(30))      
    vac_date = db.Column(db.String(20))        
    special_needs = db.Column(db.Text, default="N/A")
    other_description = db.Column(db.Text)
    status = db.Column(db.String(20), default="Available")
    requests = db.relationship('AdoptionRequest', backref='pet', cascade="all, delete", lazy=True)

class AdoptionRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id', ondelete='CASCADE'), nullable=False)
    adopter_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    id_proof = db.Column(db.String(200), nullable=False)

class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    force_password_change = db.Column(db.Boolean, default=False)
    is_default = db.Column(db.Boolean, default=False)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_username = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(255), nullable=False) 
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# --- 3. UTILITIES & DATABASE INITIALIZATION ---

def get_current_admin():
    admin_id = session.get('admin_id')
    if admin_id:
        return db.session.get(AdminUser, admin_id)
    return None

def log_action(action_text):
    curr = get_current_admin()
    if curr:
        log = AuditLog(admin_username=curr.username, action=action_text)
        db.session.add(log)
        db.session.commit()

def save_upload(file):
    if not file or file.filename == "": return None, "No file selected."
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext[1:] not in ALLOWED_EXTENSIONS: return None, "Invalid file type."
    unique_name = f"{uuid4().hex}{ext}"
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
    return unique_name, None

def is_authentic_email(email):
    return re.fullmatch(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email or "")

def is_valid_name(name, max_len=100):
    return name and len(name) <= max_len and re.fullmatch(r"[A-Za-z][A-Za-z\s'\-\.]{1,}", name)

def is_valid_username(u, max_len=50):
    return u and len(u) <= max_len and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_\-\.]{2,}", u)

def is_strong_password(p, min_len=8):
    return p and len(p) >= min_len

with app.app_context():
    db.create_all() 
    admin_exists = db.session.execute(select(AdminUser).filter_by(username="admin")).scalar()
    if not admin_exists:
        db.session.add(AdminUser(
            username="admin", 
            password_hash=generate_password_hash("password123"), 
            force_password_change=True, 
            is_default=True
        ))
        db.session.commit()

# --- 4. ROUTES ---

@app.route('/')
def index():
    return render_template('index.html', pets=Pet.query.filter_by(status="Available").all())

@app.route('/adopt/<int:pet_id>', methods=['GET', 'POST'])
def adopt(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    if request.method == 'POST':
        name, email, file = request.form.get('name', '').strip(), request.form.get('email', '').strip().lower(), request.files.get('id_proof')
        
        # Validate formatting
        if not is_valid_name(name) or not is_authentic_email(email):
            flash("Check your formatting. Please provide a valid name and email.", "danger")
            return redirect(request.url)
            
        # Save the uploaded ID proof
        fname, err = save_upload(file)
        if err: 
            flash(err, "danger")
            return redirect(request.url)
            
        # Add adoption request to database
        new_request = AdoptionRequest(pet_id=pet.id, adopter_name=name, email=email, id_proof=fname)
        db.session.add(new_request)
        db.session.commit()
        
        # --- FLASH SUCCESS NOTICE ---
        flash(f"Application for {pet.name} submitted successfully! Our staff will review your ID and contact you via email.", "success")
        
        return redirect(url_for('adopt', pet_id=pet.id))
    return render_template('adopt.html', pet=pet)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        u, p = request.form.get('username'), request.form.get('password')
        admin = AdminUser.query.filter_by(username=u).first()
        if admin and check_password_hash(admin.password_hash, p):
            session['admin_id'] = admin.id
            return redirect(url_for('admin_dashboard'))
        flash("Invalid username or password.", "danger")
    return render_template('admin.html', login_mode=True)

@app.route('/admin/dashboard')
def admin_dashboard():
    curr_admin = get_current_admin()
    if not curr_admin: 
        flash("Please log in first.", "warning")
        return redirect(url_for('admin_login'))
    return render_template('admin.html', 
                           pets=Pet.query.all(), 
                           requests=AdoptionRequest.query.all(), 
                           logs=AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(50).all(),
                           login_mode=False)

@app.route('/admin/add_pet', methods=['POST'])
def add_pet():
    if not get_current_admin(): return redirect(url_for('admin_login'))
    file = request.files.get('photo')
    filename, error = save_upload(file)
    if error:
        flash(error, "danger")
        return redirect(url_for('admin_dashboard'))
    
    new_pet = Pet(
        name=request.form.get('name'), breed=request.form.get('breed'),
        age_category=request.form.get('age_category'), gender=request.form.get('gender'),
        size=request.form.get('size'), energy_level=request.form.get('energy_level'),
        spayed_neutered=request.form.get('spayed_neutered'), vac_status=request.form.get('vac_status'),
        vac_date=request.form.get('vac_date'), special_needs=request.form.get('special_needs') or "N/A",
        other_description=request.form.get('other_description'), photo=filename
    )
    db.session.add(new_pet)
    db.session.commit()
    log_action(f"Registered new pet: {new_pet.name}")
    flash("Pet added!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_pet/<int:pet_id>', methods=['GET', 'POST'])
def edit_pet(pet_id):
    if not get_current_admin(): return redirect(url_for('admin_login'))
    pet = Pet.query.get_or_404(pet_id)
    if request.method == 'POST':
        pet.name = request.form.get('name')
        pet.breed = request.form.get('breed')
        pet.age_category = request.form.get('age_category')
        pet.gender = request.form.get('gender')
        pet.size = request.form.get('size')
        pet.energy_level = request.form.get('energy_level')
        pet.spayed_neutered = request.form.get('spayed_neutered')
        pet.vac_status = request.form.get('vac_status')
        pet.vac_date = request.form.get('vac_date')
        pet.special_needs = request.form.get('special_needs')
        pet.other_description = request.form.get('other_description')
        pet.status = request.form.get('status')
        file = request.files.get('photo')
        if file and file.filename != '':
            new_img, err = save_upload(file)
            if not err:
                if pet.photo: 
                    try: os.remove(os.path.join(app.config['UPLOAD_FOLDER'], pet.photo))
                    except: pass
                pet.photo = new_img
        db.session.commit()
        log_action(f"Updated profile for: {pet.name}")
        flash("Pet updated!", "success")
        return redirect(url_for('admin_dashboard'))
    return render_template('edit_pet.html', pet=pet)

@app.route('/admin/delete_pet/<int:pet_id>')
def delete_pet(pet_id):
    if not get_current_admin(): return redirect(url_for('admin_login'))
    pet = Pet.query.get_or_404(pet_id)
    pet_name = pet.name
    if pet.photo:
        try: os.remove(os.path.join(app.config['UPLOAD_FOLDER'], pet.photo))
        except: pass
    db.session.delete(pet)
    db.session.commit()
    log_action(f"Permanently removed pet: {pet_name}")
    flash("Pet removed.", "info")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/admins', methods=['GET', 'POST'])
def admin_accounts():
    curr = get_current_admin()
    if not curr: 
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        u = request.form.get('username', '').strip()
        p = request.form.get('password')
        c = request.form.get('confirm_password')

        # 1. Check if passwords match
        if p != c:
            flash("Passwords do not match. Please try again.", "danger")
        
        # 2. Check password strength
        elif not is_strong_password(p):
            flash("Password is too weak. It must be at least 8 characters long.", "danger")
            
        # 3. Check username format
        elif not is_valid_username(u):
            flash("Invalid username. Use only letters, numbers, and .-_", "danger")
            
        # 4. Process if all validations pass
        else:
            if not AdminUser.query.filter_by(username=u).first():
                new_admin = AdminUser(
                    username=u.lower(), 
                    password_hash=generate_password_hash(p)
                )
                db.session.add(new_admin)
                db.session.commit()
                log_action(f"Created new admin account: {new_admin.username}")
                flash("Admin created!", "success")
            else:
                flash("Username already taken.", "danger")
                
    return render_template('admin_accounts.html', admins=AdminUser.query.all(), current_admin=curr)

@app.route('/admin/edit_admin/<int:admin_id>', methods=['GET', 'POST'])
def edit_admin(admin_id):
    if not get_current_admin(): return redirect(url_for('admin_login'))
    adm = db.session.get(AdminUser, admin_id)
    if request.method == 'POST':
        new_u = request.form.get('username', '').lower()
        if is_valid_username(new_u):
            existing = AdminUser.query.filter(AdminUser.username == new_u, AdminUser.id != admin_id).first()
            if not existing:
                old_u = adm.username
                adm.username = new_u
                pw = request.form.get('password')
                if pw and is_strong_password(pw): adm.password_hash = generate_password_hash(pw)
                db.session.commit()
                log_action(f"Modified admin identity: {old_u} to {new_u}")
                flash("Account updated!", "success")
                return redirect(url_for('admin_accounts'))
    return render_template('edit_admin.html', admin=adm)

@app.route('/admin/delete_admin/<int:admin_id>')
def delete_admin(admin_id):
    curr = get_current_admin()
    if curr and curr.id != admin_id:
        adm = db.session.get(AdminUser, admin_id)
        target_name = adm.username
        db.session.delete(adm)
        db.session.commit()
        log_action(f"Revoked access for admin: {target_name}")
        flash("Admin deleted.", "info")
    return redirect(url_for('admin_accounts'))

@app.route('/admin/approve/<int:req_id>')
def approve(req_id):
    if not get_current_admin(): return redirect(url_for('admin_login'))
    
    req = db.session.get(AdoptionRequest, req_id)
    if req:
        pet = db.session.get(Pet, req.pet_id)
        pet.status = "Adopted"
        
        # Capture details before deleting the request
        recipient_email = req.email
        adopter_name = req.adopter_name
        pet_name = pet.name

        try:
            # Create the Automated Email
            msg = Message(f"Official Approval: Application for {pet_name}",
                          recipients=[recipient_email])
            
            google_form_link = "https://forms.gle/d7ryfkXgzGLRyNWo7"

            msg.body = f"""Dear {adopter_name},

Congratulations! We are pleased to inform you that your formal application to adopt {pet_name} has been APPROVED by the PetAdopt Staff.

As part of our commitment to professional animal welfare and streamlined processing, please complete the following final steps:

1. DIGITAL ADOPTION AGREEMENT
Please review and submit our official adoption agreement here before your visit: {google_form_link}

Note: By submitting this form, you skip the manual paperwork phase at our Marikina City Sanctuary office.
Deadline: You have one month from today to submit this form. Incomplete applications after 30 days will be considered void.

2. SCHEDULE FOR PICKUP
Once your form is submitted, you may visit us for the handover. Our sanctuary is open during the following hours:

Monday to Friday: 9:00 AM – 4:00 PM
Saturday: 10:00 AM – 2:00 PM
Closed on Sundays and Public Holidays.

3. DOCUMENTS & RECORDS

Verification: Upon arrival, please present the original physical Government ID that you used for your digital application.
Medical Files: All official vaccination and medical history records will be handed over to you during the physical pickup.


CONTACT & LOCATION DETAILS
After submitting your form, you may proceed to our sanctuary at the address below:

Address: Marikina City, Philippines
Phone: +63 912 345 6789
Email: thepetadoption@gmail.com  

We look forward to meeting you soon!

Best regards,

Patch & The PetAdopt Team Marikina City, Philippines
"""
            mail.send(msg)
            flash(f"Approval email sent to {recipient_email}!", "success")
        except Exception as e:
            flash(f"System approved the request, but the email failed to send: {str(e)}", "warning")
        log_action(f"Approved adoption for {pet.name} by {adopter_name}")
        db.session.delete(req)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/decline/<int:req_id>')
def decline(req_id):
    if not get_current_admin(): 
        return redirect(url_for('admin_login'))
    
    req = db.session.get(AdoptionRequest, req_id)
    if req:
        adopter_name = req.adopter_name
        recipient_email = req.email
        pet_name = req.pet.name if req.pet else "the pet"

        try:
            msg = Message(f"Update regarding your application for {pet_name}",
                          recipients=[recipient_email])
            
            msg.body = f"""Dear {adopter_name},

Thank you for your interest in adopting from PetAdopt and for taking the time to submit an application for {pet_name}.

After a careful review of all applications by our staff, we have decided not to move forward with your request at this time. Our selection process is designed to ensure the most compatible match for the specific needs of each animal in our care.

Please do not let this discourage you from following our gallery, as new companions arrive frequently. We appreciate your heart for animal welfare.

Best regards,
The PetAdopt Team
Marikina City, Philippines
"""
            mail.send(msg)
            flash(f"Decline notice sent to {recipient_email}.", "info")
        except Exception as e:
            flash(f"Request removed, but email failed: {str(e)}", "warning")

        log_action(f"Declined adoption request from {adopter_name}")
        db.session.delete(req)
        db.session.commit()
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def logout():
    session.pop('admin_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':  
    app.run(debug=True)