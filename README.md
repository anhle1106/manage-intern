# DevOps Intern Management Platform

An internal management platform built for managing DevOps interns, featuring schedule tracking, leave management, onboarding cohorts, training document upload via Cloudinary, and AI-powered learning roadmap generation using Gemini API.

---

## 🛠 Tech Stack

- **Backend**: Python 3.11, FastAPI, Pydantic v2, Motor (Async MongoDB), PyMuPDF (PDF), python-docx (DOCX), Google Generative AI SDK, Cloudinary SDK
- **Frontend**: Vanilla HTML5, Vanilla CSS3 (Custom Design System), Vanilla JavaScript (ES6+ Fetch API), FullCalendar v6
- **Database**: MongoDB Atlas Free Tier / MongoDB
- **Deployment**: Docker & Docker Compose with Nginx reverse proxy

---

## 📁 Architecture (Domain-Module)

```
manage-intern/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app setup & router registration
│   │   ├── config.py            # Environment configuration (Pydantic Settings)
│   │   ├── database.py          # Motor async MongoDB client & lifecycle
│   │   │
│   │   ├── common/              # Shared enums, dependencies, response helpers
│   │   ├── auth/                # JWT Login & Auth routes/service
│   │   ├── users/               # Account CRUD (Admin only)
│   │   ├── interns/             # Intern profile management
│   │   ├── schedules/           # University schedule tracking & occupied check
│   │   ├── leave_requests/      # Leave request lifecycle (Submit → Approve/Reject)
│   │   ├── onboardings/         # Onboarding batch cohorts & member assignment
│   │   ├── documents/           # Cloudinary file upload & text extraction
│   │   ├── ai/                  # Gemini AI document topic extraction module
│   │   ├── learning/            # Learning roadmap & completion progress
│   │   ├── dashboard/           # Role-based dashboard aggregations
│   │   └── seed.py              # Seed script for demo accounts & sample data
│   │
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── index.html               # Auth redirect
│   ├── login.html               # Login interface
│   ├── dashboard.html           # Dynamic role dashboard
│   ├── schedule.html            # FullCalendar schedule view
│   ├── leave.html               # Leave request table & creation modal
│   ├── onboarding.html          # Onboarding batch cohort cards
│   ├── documents.html           # Document upload & processing status
│   ├── learning.html            # Interactive learning roadmap
│   ├── users.html               # User administration (Admin only)
│   ├── css/style.css            # Dark theme design system
│   └── js/                      # Page scripts & API client
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🚀 Quick Start with Docker

### 1. Environment Setup

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Environment variables:

```env
MONGODB_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/intern_management?retryWrites=true&w=majority
JWT_SECRET=your-secure-random-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret

GEMINI_API_KEY=your_gemini_api_key
```

### 2. Launch Services

```bash
docker compose up --build -d
```

The services will be available at:
- **Frontend App**: `http://localhost` (or `http://localhost:80`)
- **Backend API**: `http://localhost:8000`
- **Swagger API Docs**: `http://localhost:8000/docs`

### 3. Populate Seed Data

Run the seed script inside the running backend container to generate demo accounts and initial data:

```bash
docker compose exec backend python -m app.seed
```

---

## 🔑 Default Seed Accounts

After running the seed script, you can log in using these default credentials:

| Role | Email | Password | Scope / Capabilities |
|---|---|---|---|
| **ADMIN** | `admin@devops.com` | `Admin@123` | Full access: User management, Batch creation, Member assignment, Document uploads |
| **LEADER** | `leader1@devops.com` | `Leader@123` | Batch leader access: View assigned interns, review leave requests, view roadmaps |
| **INTERN** | `intern1@devops.com` | `Intern@123` | Intern access: Manage schedule, submit leave requests, view roadmap & mark completed |

---

## 🔒 Role-Based Access Control (RBAC)

RBAC is enforced at the FastAPI backend middleware level via dependency injection (`require_roles`):

- **ADMIN**: Access to all endpoints, user creation/deletion, batch management, document uploads.
- **LEADER**: View assigned interns, review leave requests from assigned interns, view roadmaps.
- **INTERN**: Manage own schedule, submit/cancel own leave requests, view assigned batch roadmaps, mark topic completion.
