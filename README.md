# TinyTrack

TinyTrack is a full-stack Django-based nursery management system designed to streamline communication, attendance tracking, student management, and daily activity monitoring within nursery and preschool environments.

The platform provides separate dashboards for teachers and parents, enabling efficient management of student records, attendance, reports, notifications, and classroom activities.

---

# Features

## Student Management

* Add and manage student profiles
* Maintain student information records
* View individual student details

## Attendance Tracking

* Daily attendance management
* Attendance status monitoring
* Teacher-controlled attendance updates

## Parent Dashboard

* View student information
* Access daily reports and updates
* Receive notifications and announcements
* Monitor student activities

## Teacher Dashboard

* Manage students and attendance
* Upload reports and updates
* Communicate with parents
* Track classroom activities

## Daily Reports

* Generate and manage daily student reports
* Share progress and classroom activities with parents

## Communication System

* Parent-teacher interaction support
* Notifications and updates system
* Chat and messaging functionality

---

# Tech Stack

| Technology | Usage                     |
| ---------- | ------------------------- |
| Python     | Backend Programming       |
| Django     | Web Framework             |
| SQLite     | Database                  |
| HTML/CSS   | Frontend                  |
| JavaScript | Client-side Functionality |

---

# Project Structure

```text
TinyTrack/
│
├── nursery/
│   ├── templates/
│   ├── migrations/
│   ├── views.py
│   ├── models.py
│   └── urls.py
│
├── tinytrack/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── manage.py
├── requirements.txt
└── README.md
```

---

# Installation

## 1. Clone the Repository

```bash
git clone https://github.com/melvinmv02/TinyTrack.git
```

Move into the project directory:

```bash
cd TinyTrack
```

---

## 2. Create Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Apply Migrations

```bash
python manage.py migrate
```

---

## 5. Create Superuser

```bash
python manage.py createsuperuser
```

---

## 6. Run the Development Server

```bash
python manage.py runserver
```

Open the application in your browser:
http://127.0.0.1:8000/

# Future Improvements

* Email notification integration
* Real-time chat system
* Cloud database deployment
* Mobile responsiveness improvements
* Role-based access control enhancements
* Analytics dashboard


# Learning Outcomes

This project demonstrates practical implementation of:

* Django MVC architecture
* Authentication and authorization
* Database management with SQLite
* CRUD operations
* Template rendering
* Parent-teacher communication workflows
* Web application development best practices


**Melvin Mathew**

GitHub: [https://github.com/melvinmv02](https://github.com/melvinmv02)


This project is developed for educational and academic purposes.
