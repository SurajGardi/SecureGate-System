
# 🛡️ SecureGate - Visitor Management System

SecureGate is a smart visitor management system for residential societies. Built with **Python**, **MySQL**, **HTML**, and **CSS**, it offers role-based access, real-time visitor approvals, photo verification, email alerts, and secure digital logs for enhanced security and convenience.

---

## 📦 Repository

**Project Repository:** [https://github.com/SurajGardi/SecureGate-System.git](https://github.com/SurajGardi/SecureGate-System.git)

---

## ✨ Features

✔ Role-Based Access for Admins, Guards, and Flat Owners  
✔ Guard can register visitors with photo capture  
✔ Flat Owners receive email alerts for visitor approval  
✔ Admin dashboard for system monitoring and user management  
✔ Digital visitor logs with entry/exit tracking  
✔ Modular and easy-to-deploy system  

---

## 🏗️ Project Structure

```
SECUREGATE_PROJECT/
│
├── static/                # Static files (JS, CSS, images)
│   └── js/
│       └── otp_verification.js
│
├── templates/             # Frontend HTML templates
│   ├── Admin1.html
│   ├── Flat-Owner.html
│   ├── Guard.html
│   └── signup.html
│
├── admin.py               # Admin role logic
├── flat_owner.py          # Flat Owner role logic
├── guard.py               # Guard role logic
├── mail.py                # Email configuration and sending
├── main.py                # Application entry point
├── signin.py              # Sign-in functionality
├── signup.py              # Sign-up functionality
│
├── securegate_db.sql      # MySQL database structure
├── new_Project.sql        # Additional database setup (if applicable)
│
├── requirements.txt       # Python dependencies
└── requirement.txt        # (Optional, duplicate of above)
```

---

## 🖥️ Tech Stack

- **Programming Language:** Python  
- **Framework:** Web-based architecture using Python tools  
- **Database:** MySQL (recommended port: 3333)  
- **Frontend:** HTML5, CSS3  
- **Email Service:** SMTP (e.g., Gmail)  
- **Version Control:** Git & GitHub  

---

## ⚙️ Installation & Setup Guide

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/SurajGardi/SecureGate-System.git
cd SecureGate-System
```

### 2️⃣ Create Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Setup MySQL Database

- Open MySQL Workbench or preferred tool  
- Run `securegate_db.sql` to create required tables  

💡 **Note:** Ensure MySQL is running on port `3333` or update connection details in code.

### 5️⃣ Configure Email (SMTP)

In `mail.py`, add your email credentials for sending approval emails:

```python
EMAIL_ADDRESS = 'your-email@gmail.com'
EMAIL_PASSWORD = 'your-app-password'
```

⚠️ Use Gmail **App Passwords**. Never hardcode real passwords in production.

### 6️⃣ Run the Application

```bash
python main.py
```

Visit the app at:  
```
http://127.0.0.1:5000
```

---

## 👥 User Roles

| Role         | Description                                           |
|--------------|-------------------------------------------------------|
| **Admin**    | Manages users, monitors system, views visitor logs    |
| **Guard**    | Registers visitors, captures photos, manages entry    |
| **Flat Owner** | Approves/rejects visitors via email, views history |

---

## 🔒 Future Enhancements

- Mobile App for real-time notifications  
- Two-Factor Authentication (2FA)  
- Face Recognition for visitor identification  
- Advanced Analytics & Dashboards  
- Cloud-based data backup  

---

## 📄 License

Developed as part of academic project at **Fergusson College, Pune**.  
Feel free to explore, enhance, and contribute.

---

## 🙌 Acknowledgements

Guided by: **Dr. Aparna Vaidynathan**  
Project Members:  
- **Sakshi Jamdade**  
- **Suraj Gardi**  
