# NutriAI Project - Clean Structure

## Final Project Layout

```
nutriaiproject/
├── core/                          # Main Django application
│   ├── api/                       # REST API v1 endpoints
│   │   ├── __init__.py
│   │   ├── nutritionist.py        # Chat API endpoints
│   │   ├── fastapi_client.py      # FastAPI integration
│   │   ├── routes/                # Additional API routes
│   │   └── v1.py                  # Main API router (health assessment, chat, PDF)
│   ├── management/commands/       # Django management commands
│   │   ├── __init__.py
│   │   ├── runserver.py           # Auto-start Qwen with Django
│   │   └── start_qwen.py          # Start Qwen server
│   ├── migrations/                # Database migrations
│   ├── __init__.py
│   ├── admin.py                   # Django admin configuration
│   ├── apps.py                    # App configuration
│   ├── models.py                  # Database models
│   ├── views.py                   # View handlers
│   ├── urls.py                    # URL routing
│   ├── utils.py                   # Utility functions (BMI, health tips, validation)
│   ├── tracking_utils.py          # Usage tracking and stats
│   ├── api.py                     # API router setup
│   ├── qwen_client.py             # Qwen AI client
│   ├── local_qwen_server.py       # Local Qwen server setup
│   └── meal_suggestions.py        # Meal suggestion generation with JSON repair
│
├── health_chat_ai/                # Django project configuration
│   ├── __init__.py
│   ├── settings.py                # Django settings (with Qwen config)
│   ├── urls.py                    # Project-level URL routing
│   ├── wsgi.py                    # WSGI entry point
│   └── asgi.py                    # ASGI entry point
│
├── templates/                     # HTML templates
│   └── core/
│       ├── home.html              # Landing page (cartoon UI)
│       ├── login.html             # Login form
│       ├── register.html          # Registration form
│       ├── health_assesment.html  # Health assessment form & results
│       ├── chat.html              # AI chat interface
│       ├── profile.html           # User profile
│       ├── assessment_history.html
│       ├── assessment_detail.html
│       ├── delete_account_confirm.html
│       └── test_ocr.html          # OCR testing page
│
├── static/                        # Static files
│   ├── css/                       # Stylesheets (cartoon styling)
│   ├── js/                        # JavaScript files
│   └── images/                    # Images and icons
│
├── docs/                          # Documentation
│   ├── INDEX.md                   # Project overview & structure
│   ├── README.md                  # Main readme
│   ├── QUICK_START.md             # Quick setup guide
│   ├── QUICK_REFERENCE.md         # API & feature reference
│   └── [other docs]               # Historical documentation
│
├── logs/                          # Application logs
│   ├── django_dev.log
│   ├── local_qwen.log
│   └── [other logs]
│
├── .env                           # Environment configuration
├── .env.example                   # Example env template
├── .gitignore                     # Git ignore rules
├── manage.py                      # Django CLI
├── db.sqlite3                     # SQLite database
├── requirements.txt               # Python dependencies
└── start_qwen_server.sh           # Qwen server startup script
```

## Files Removed (Nov 23 Cleanup)

### Unnecessary Files Deleted:
- ✅ `test_ocr_minimal.html` - Test file
- ✅ `core/tests.py` - Empty placeholder test file
- ✅ `core/nutrition_db.py` - Unused nutrition database (functions replaced)
- ✅ `start_all.sh` - Redundant startup script
- ✅ `tools/` directory - Unused model utilities
- ✅ `ai_service/` directory - Duplicate/obsolete code
- ✅ `nutriaiproject/` directory - Empty duplicate
- ✅ `models/` directory with backups - Obsolete backups
- ✅ `.venv.orig/` - Old virtual environment
- ✅ All `.log`, `.out`, `.pid` files from root
- ✅ Multiple markdown documentation files (archived to `docs/`)
- ✅ Duplicate `@login_required` decorators in views.py

## Essential Files Only

### Core Application (Required for operation):
- `manage.py` - Django management
- `db.sqlite3` - Database
- `requirements.txt` - Dependencies
- `.env` - Configuration

### Core App Files (Required for features):
- `models.py` - Data models
- `views.py` - Request handlers
- `urls.py` - URL routing
- `api.py` - API router
- `utils.py` - Business logic
- `meal_suggestions.py` - AI meal generation
- `qwen_client.py` - Qwen integration
- `local_qwen_server.py` - Local AI setup
- `tracking_utils.py` - User tracking

### Django Config (Required):
- `health_chat_ai/settings.py` - Django config
- `health_chat_ai/urls.py` - Project URLs
- `health_chat_ai/wsgi.py` - Production server
- `health_chat_ai/asgi.py` - Async server

### Templates & Static (Required for UI):
- All files in `templates/core/`
- All files in `static/`

### Scripts (Optional but useful):
- `start_qwen_server.sh` - Start AI backend
- `core/management/commands/runserver.py` - Auto-start Qwen

## Project Size Before/After

**Before:** ~217 files, cluttered root with logs and docs
**After:** ~100 files, organized structure, all dependencies clear

## Running the Project

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start with auto-Qwen startup
python manage.py runserver

# Or start manually
bash start_qwen_server.sh  # Terminal 1
python manage.py runserver # Terminal 2
```

## Dependencies (requirements.txt)
- Django 5.2.7
- ninja (REST API framework)
- Pillow (OCR image processing)
- pytesseract (OCR)
- ReportLab (PDF generation)
- requests (HTTP client)

---
Last Updated: November 23, 2025
Project Status: Clean, Organized, Production-Ready ✅
