# 🐾 PetAdopt: Professional Animal Welfare Management System

An aesthetic, high-security, and feature-rich web platform designed to streamline the transition between animal sanctuaries and responsible guardians. Built as a comprehensive full-stack project, this system focuses on **verified security, medical transparency, and automated communication.**

---

## ✨ Advanced Features
* **Professional Gallery:** High-fidelity profiles featuring detailed breed data, energy levels, and size categories.
* **Clinical Records Tracking:** Manage vaccination statuses, sterilization (spay/neuter) records, and medical history dates directly in the database.
* **Automated Email Engine:** Automatically sends professional approval/decline notices to adopters via SMTP, including next-step instructions and Google Form links.
* **Secured Staff Portal:** Protected Admin Dashboard for inventory management and adoption request processing.
* **Audit Logging:** Every administrative action (pet registration, profile updates, account deletions) is timestamped and logged for accountability.
* **Government ID Verification:** Mandatory digital ID uploads processed through a secure file-handling system.

## 🛠️ Tech Stack
* **Backend:** Python 3.10+ (Flask Framework)
* **Database:** **MySQL** (leveraging SQLAlchemy ORM for relational integrity)
* **Frontend:** HTML5, CSS3 (Custom "Heritage" Aesthetic), Bootstrap 5.3
* **Communication:** Flask-Mail (SMTP Integration)
* **Security:** Werkzeug (Password Hashing), UUID (Unique File Obfuscation), and Secure Session Management

## 📂 System Architecture
```text
pet_adoption_system/
├── app.py                 # Core Engine: Routes, Models, & Email Logic
├── requirements.txt       # System Dependencies
├── static/
│   ├── style.css          # Custom Styling (Playfair Display/Inter Fonts)
│   └── uploads/           # Obfuscated Storage for IDs & Pet Photos
└── templates/
    ├── index.html         # Public Landing Page & Journey
    ├── adopt.html         # Formal Application Form
    ├── admin.html         # Unified Staff Login & Dashboard
    ├── admin_accounts.html# Staff Access & Permission Management
    └── edit_pet.html      # Clinical Record Management Interface




🚀 Deployment & Installation
1. Configure MySQL Database
Create a database named pet_adoption in your MySQL environment. The system is configured to connect via: mysql+pymysql://root:@localhost/pet_adoption

2. Install Dependencies
Run the following command in your terminal:

Bash
pip install -r requirements.txt
3. Setup SMTP (Email)
To enable the automated email feature:

Enable "App Passwords" in your Google Account security settings.

Update the MAIL_PASSWORD in app.py with your 16-character code.

4. Launch System
Bash
python app.py
Default Admin Credentials: * User: admin

Pass: password123

Note: The system will prompt you to change this upon your first successful login.

📍 Contact & Credits
Developer: Patch

Location: Marikina City, Philippines

Mission: Standardizing pet welfare through modern technology.

