# FitWell - AI-Powered Nutrition & Health Assistant

![FitWell Banner](https://img.shields.io/badge/FitWell-AI%20Nutrition%20Assistant-00e5ff?style=for-the-badge)
![Django](https://img.shields.io/badge/Django-5.2.7-092E20?style=flat&logo=django)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

A modern, intelligent nutrition and health tracking application powered by AI. FitWell helps users manage their nutrition, get personalized meal plans, track health metrics, and receive expert advice through an AI-powered coach.

## 🌟 Features

### 🤖 AI Coach (Ask Coach)
- Real-time conversational AI nutritionist powered by Qwen LLM
- Personalized nutrition advice and meal planning
- Context-aware responses based on user health profile
- Multi-language support

### 📊 Body Analysis
- BMI calculation with personalized insights
- Health metrics tracking (weight, height, body composition)
- Progress visualization and historical data
- Custom health recommendations based on BMI category

### 📱 Dashboard
- Clean, modern interface with dark theme
- Quick access to all features
- Health statistics overview
- Recent activity tracking

### 👤 My Account
- User profile management
- Health data tracking over time
- Progress reports and analytics
- Account settings and preferences

### 🎨 Modern UI/UX
- Beautiful dark theme with cyan/navy color palette
- Responsive design for all devices
- Smooth animations and transitions
- Glassmorphism effects

## 🚀 Tech Stack

- **Backend**: Django 5.2.7
- **AI Model**: Qwen 1.5 0.5B (Local inference)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Database**: SQLite (development), PostgreSQL-ready (production)
- **Styling**: Custom CSS with Tailwind CSS utilities
- **Icons**: Font Awesome 6.4.0

## 📋 Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Virtual environment tool (venv, conda, etc.)
- 4GB+ RAM (for AI model)
- Modern web browser

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/minhaz-42/fitwell.git
cd fitwell
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (optional - uses SQLite by default)
# DATABASE_URL=postgresql://user:password@localhost:5432/fitwell

# Email Configuration (optional)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# AI Model Settings
QWEN_LOCAL_MODEL_PATH=models/Qwen
QWEN_LOCAL_PORT=21002
QWEN_DEVICE=cpu
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 7. Download AI Model

Download Qwen 1.5 0.5B Chat model files and place them in `models/Qwen/`:
- Model files: https://huggingface.co/Qwen/Qwen1.5-0.5B-Chat

**Note**: The `models/` directory is excluded from git due to large file sizes.

### 8. Start the Application

```bash
# Terminal 1: Start Qwen AI Server
./start_qwen_server.sh

# Terminal 2: Start Django Development Server
python manage.py runserver
```

### 9. Access the Application

Open your browser and navigate to:
- **Main App**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **AI Model API**: http://localhost:21002 (automatically started)

## 📁 Project Structure

```
fitwell/
├── core/                      # Main Django app
│   ├── api/                   # REST API endpoints
│   │   ├── __init__.py
│   │   └── v1.py              # API v1 routes
│   ├── migrations/            # Database migrations
│   ├── models.py              # Database models
│   ├── views.py               # View controllers
│   ├── urls.py                # URL routing
│   ├── admin.py               # Admin interface
│   ├── email_utils.py         # Email functionality
│   ├── qwen_client.py         # AI model client
│   └── local_qwen_server.py   # Local AI server
├── health_chat_ai/            # Project settings
│   ├── settings.py            # Django configuration
│   ├── urls.py                # Root URL configuration
│   └── wsgi.py                # WSGI configuration
├── static/                    # Static files
│   ├── css/                   # Stylesheets
│   │   └── nourish_theme.css  # Modern dark theme
│   ├── js/                    # JavaScript files
│   └── images/                # Image assets
├── templates/                 # HTML templates
│   └── core/                  # Core app templates
│       ├── home.html          # Dashboard
│       ├── chat.html          # AI Coach
│       ├── health_assesment.html  # Body Analysis
│       ├── profile.html       # My Account
│       └── ...                # Other templates
├── models/                    # AI models (not in repo)
│   └── Qwen/                  # Qwen LLM files
├── manage.py                  # Django management
├── requirements.txt           # Python dependencies
├── start_qwen_server.sh       # AI server startup script
├── db.sqlite3                 # Database (not in repo)
└── README.md                  # This file
```

## 🎯 Key Features Explained

### AI Coach System
The AI Coach uses a local Qwen 1.5 0.5B model for:
- Personalized nutrition advice
- Meal planning suggestions
- Health Q&A
- Exercise recommendations
- Dietary guidance

### Body Analysis
Comprehensive health tracking including:
- BMI calculation and interpretation
- Weight tracking over time
- Health category assessment (Underweight, Normal, Overweight, Obese)
- Personalized recommendations based on metrics

### User Dashboard
Centralized hub featuring:
- Quick stats overview
- Recent AI conversations
- Health metrics visualization
- Easy navigation to all features

### Conversation Management
- Save and resume conversations
- View conversation history
- Search through past discussions
- Export conversation data

## 🔧 Configuration

### AI Model Setup

The Qwen model requires approximately 1.2GB of disk space. Download the model files and place them in the `models/Qwen/` directory with the following structure:

```
models/Qwen/
├── config.json
├── generation_config.json
├── model.safetensors
├── tokenizer.json
├── tokenizer_config.json
└── ... (other model files)
```

### Email Configuration

For email functionality (password reset, confirmations), configure in `.env`:

```env
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@fitwell.com
DEFAULT_FROM_NAME=FitWell
```

For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833).

### Database Configuration

**Development (SQLite - Default)**:
```python
# No configuration needed - works out of the box
```

**Production (PostgreSQL)**:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/fitwell_db
```

## 🎨 Customization

### Color Theme

The app uses a modern dark theme. Edit `static/css/nourish_theme.css` to customize:

```css
:root {
    --bg-primary: #0a1929;      /* Deep Navy */
    --bg-secondary: #132f4c;    /* Navy Blue */
    --accent-primary: #00e5ff;  /* Bright Cyan */
    --text-primary: #ffffff;    /* White */
    --success: #00e676;         /* Green */
}
```

### Branding

Update app name and branding:
- App name: Search and replace "FitWell" in templates
- Logo: Update in `templates/core/home.html`
- Footer: Edit `templates/core/home.html` footer section

## 🔒 Security Notes

**Important Security Practices**:

1. **Never commit sensitive data**:
   - `.env` files
   - Database files (`db.sqlite3`)
   - AI model files (large and sensitive)

2. **Production settings**:
   - Set `DEBUG=False`
   - Use strong `SECRET_KEY`
   - Configure proper `ALLOWED_HOSTS`
   - Use HTTPS
   - Set up CSRF protection

3. **Keep dependencies updated**:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test core

# Check for issues
python manage.py check

# Validate database
python manage.py migrate --check
```

## 📊 Database Models

### Core Models
- **User**: Extended Django user with health profile
- **HealthMetrics**: BMI, weight, height tracking
- **Conversation**: AI chat sessions
- **Message**: Individual chat messages
- **EmailConfirmation**: Email verification tokens
- **EmailLog**: Email delivery tracking
- **UserStats**: Usage analytics
- **UsageTracking**: Feature usage patterns

## 🌐 API Endpoints

### Public Endpoints
- `GET /` - Home/Dashboard
- `GET /health/` - Body Analysis page
- `GET /chat/` - AI Coach page
- `GET /profile/` - User profile page

### API Endpoints
- `POST /api/v1/chat` - Send message to AI
- `GET /api/conversations/` - List conversations
- `GET /api/profile/` - Get user profile
- `POST /api/progress-tracking/` - Save health metrics

## 🚀 Deployment

### Heroku Deployment

```bash
# Install Heroku CLI and login
heroku login

# Create app
heroku create fitwell-app

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS=fitwell-app.herokuapp.com

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Deploy
git push heroku main

# Run migrations
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser
```

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations
RUN python manage.py migrate

# Expose port
EXPOSE 8000

# Start server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "health_chat_ai.wsgi:application"]
```

Run with Docker:
```bash
docker build -t fitwell .
docker run -p 8000:8000 fitwell
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **Open a Pull Request**

### Coding Standards
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Write tests for new features
- Update documentation

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Tanvir Ahmed**

- GitHub: [@minhaz-42](https://github.com/minhaz-42)
- LinkedIn: [Tanvir Ahmed](https://www.linkedin.com/in/tanvir-ahmed-2b9809370)
- Instagram: [@_min._.haz_](https://www.instagram.com/_min._.haz_/)
- Facebook: [Tanvir Ahmed](https://www.facebook.com/share/16buZsF87d/?mibextid=wwXIfr)
- Email: tanvirahmed.minhaz1@gmail.com

## 🙏 Acknowledgments

- **Qwen Team** - For the open-source LLM
- **Django Community** - For the excellent framework
- **Tailwind CSS** - For utility-first CSS
- **Font Awesome** - For beautiful icons
- **All Contributors** - Thank you!

## 📞 Support

Having issues? Need help?

- **Email**: tanvirahmed.minhaz1@gmail.com
- **GitHub Issues**: [Open an issue](https://github.com/minhaz-42/fitwell/issues)

## 🗺️ Roadmap

Future enhancements planned:

- [ ] Multi-language UI support (Bengali, Spanish, French)
- [ ] Mobile app (React Native/Flutter)
- [ ] Advanced meal planning with recipes database
- [ ] Integration with fitness trackers (Fitbit, Apple Health)
- [ ] Social features (share progress, challenges)
- [ ] Nutrition database expansion
- [ ] Voice input for AI Coach
- [ ] Barcode scanner for food logging
- [ ] Weekly meal prep suggestions
- [ ] Grocery list generator

## ⚡ Performance Tips

1. **Use caching** for static content
2. **Optimize database queries** with select_related/prefetch_related
3. **Use pagination** for large datasets
4. **Compress static files** in production
5. **Use CDN** for static assets
6. **Enable browser caching**

## 🐛 Known Issues

- AI model requires 4GB+ RAM
- Initial model loading takes 20-30 seconds
- Model files are large (~1.2GB) and not included in repo

## 💡 Tips & Tricks

### Quick Commands
```bash
# Reset database
rm db.sqlite3
python manage.py migrate

# Create test users
python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.create_user('test', 'test@example.com', 'testpass123')

# Check for migration issues
python manage.py makemigrations --check --dry-run

# Collect static files
python manage.py collectstatic
```

### Development Workflow
1. Make changes to code
2. Run tests: `python manage.py test`
3. Check code quality: `flake8 .` (if installed)
4. Commit with descriptive message
5. Push to your branch

---

**Made with ❤️ by Tanvir Ahmed**

*FitWell - Your AI-Powered Path to Better Health*
