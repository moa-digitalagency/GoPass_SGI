# GO-PASS SGI-GP - Systeme de Gestion Integree

## Overview
GO-PASS SGI-GP is an integrated pass management system built with Flask, PostgreSQL, and Tailwind CSS. It allows organizations to issue, manage, and validate access passes with QR codes.

## Project Structure
```
/
├── algorithms/      # Business logic algorithms
├── config/          # Configuration files
├── docs/            # Documentation
├── lang/            # Language translations (fr, en)
├── models/          # SQLAlchemy database models
├── routes/          # Flask blueprints/routes
├── scripts/         # Utility scripts
├── security/        # Authentication/authorization
├── services/        # Business services
├── statics/         # Static files
│   ├── css/        # Stylesheets
│   ├── js/         # JavaScript modules
│   ├── img/        # Images
│   └── uploads/    # User uploads (QR codes)
├── templates/       # HTML templates
├── utils/           # Helper functions
├── app.py          # Main application entry
├── init_db.py      # Database initialization
└── requirements.txt # Python dependencies
```

## Tech Stack
- **Backend**: Python 3.11+ with Flask
- **Database**: PostgreSQL
- **Frontend**: HTML5, JavaScript (ES6), Tailwind CSS
- **Authentication**: Flask-Login with role-based access

## User Roles
1. **Admin**: Full system access, can manage users and pass types
2. **Agent**: Can issue passes and validate access
3. **Holder**: Can view their own passes

## Default Credentials
- Admin: `admin` / `admin123`
- Agent: `agent` / `agent123`

## Key Features
- User management with role-based access control
- Pass generation with QR codes
- Pass validation interface (manual + QR scanner)
- Dashboard with statistics
- Access logging and audit trail
- Multi-language support (French/English)

## Running the Application
The application runs on port 5000. Initialize the database first with:
```bash
python init_db.py
```

Then start the server:
```bash
python app.py
```

## Recent Changes
- Initial setup of GO-PASS SGI-GP system
- Created complete folder structure as specified
- Implemented user management, pass management, and validation features
- Added QR code generation and scanning capabilities
- Created responsive UI with Tailwind CSS
