# 🏛️ Nagarawa — Civic Complaint Management Platform

A state-level citizen complaint platform built with Django. Users can post complaints by department, vote, comment, and track resolution status. Admins can manage, triage, and update complaints through a powerful admin panel.

---

## Features

- 📢 **Social Feed** — Post, browse, upvote/downvote, and comment on complaints
- 🏛️ **Departments** — Water, Roads, Electricity, Health, and more
- 📍 **Map Integration** — Leaflet.js + OpenStreetMap (free, no API key needed)
- 🔄 **Status Tracking** — Pending → Verified → In Progress → Solved / Rejected
- 🧑‍💼 **Admin Panel** — Review complaints, bulk update status, moderate comments
- 🕵️ **Anonymous Posting** — Users can post without revealing identity
- 💬 **Nested Comments** — Threaded replies on complaints
- 👤 **User Profiles** — Avatar, district, ward, complaint history

---

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Django 4.2 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Map | Leaflet.js + OpenStreetMap + Nominatim |
| Auth | Django built-in + custom User model |
| Styling | Vanilla CSS (no framework needed) |
| Fonts | Sora + DM Sans (Google Fonts) |

---

## Quick Setup

### 1. Clone / unzip and enter directory
```bash
cd nagarawa
```

### 2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run migrations
```bash
python manage.py makemigrations accounts
python manage.py makemigrations departments
python manage.py makemigrations complaints
python manage.py makemigrations comments
python manage.py migrate
```

### 5. Seed departments
```bash
python manage.py seed_departments
```

### 6. Create superuser (admin)
```bash
python manage.py createsuperuser
```

### 7. Run the development server
```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000

Admin panel: http://127.0.0.1:8000/admin

---

## Project Structure

```
nagarawa/
├── nagarawa/           # Project settings, URLs, wsgi
├── accounts/           # Custom user model, auth views
├── complaints/         # Core: complaint CRUD, voting, feed
├── comments/           # Comment + reply system
├── departments/        # Department model + seed command
├── core/               # Home page, context processors
├── templates/          # Base HTML template
├── static/
│   ├── css/main.css    # All styles
│   └── js/main.js      # Voting, map picker, reply toggle
├── media/              # User uploads (avatars, complaint images)
└── requirements.txt
```

---

## Admin Guide

Log into `/admin` with your superuser credentials.

### Managing Complaints
- **Filter** by department, status, date
- **Bulk actions**: Mark as Verified / In Progress / Solved / Rejected
- **Status log**: Every status change is automatically recorded with who changed it and when
- **Admin note**: Internal note field not visible to public

### Managing Comments
- Approve, hide, or flag comments for review
- Bulk approve or remove

### Managing Departments
- Add/edit/remove departments
- Toggle active/inactive

---

## Roadmap (Suggested Next Features)

| Feature | Description |
|---|---|
| Notifications | Alert users when their complaint status changes |
| Email verification | Confirm user emails on registration |
| Search | Full-text search with ElasticSearch or PostgreSQL FTS |
| API | Django REST Framework endpoints for mobile app |
| SMS alerts | Twilio integration for status SMS |
| Analytics dashboard | Charts for complaint trends by dept/status |
| Export | Download complaints as CSV/PDF |
| PWA | Progressive Web App for mobile users |

---

## Production Checklist

- [ ] Set `DEBUG = False` in settings
- [ ] Set a strong `SECRET_KEY` via environment variable
- [ ] Switch to PostgreSQL
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up static file serving (WhiteNoise or nginx)
- [ ] Configure media file storage (S3 or similar)
- [ ] Add email backend for password reset

---

## Map Notes

This project uses **Leaflet.js** with **OpenStreetMap tiles** — completely free with no API key required.

- Location picking uses the browser's built-in Geolocation API
- Reverse geocoding uses **Nominatim** (OSM's free geocoding service)
- Nominatim has a usage policy: max 1 request/second, must add attribution

---

Built with ❤️ for civic accountability.
