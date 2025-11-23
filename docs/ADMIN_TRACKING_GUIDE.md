# NutriAI Admin & Usage Tracking Documentation

## Overview

This document explains how to set up and use the Django admin interface for managing your NutriAI application and tracking user engagement.

## Table of Contents
1. [Admin Setup](#admin-setup)
2. [Access the Admin Panel](#access-the-admin-panel)
3. [Models Overview](#models-overview)
4. [Usage Tracking](#usage-tracking)
5. [User Statistics](#user-statistics)
6. [Admin Features](#admin-features)

---

## Admin Setup

### Create a Superuser Account

Before accessing the admin panel, you need to create a superuser account:

```bash
cd /Users/tanvir/Desktop/nutriaiproject
python3 manage.py createsuperuser
```

Follow the prompts to enter:
- **Username**: Your admin username (e.g., `admin`)
- **Email**: Your admin email address
- **Password**: A strong password
- **Password confirmation**: Repeat the password

Alternatively, use the provided setup script:

```bash
bash setup_admin.sh
```

---

## Access the Admin Panel

### Start the Development Server

```bash
python3 manage.py runserver
```

### Visit the Admin Panel

1. Open your browser
2. Navigate to: `http://localhost:8000/admin/`
3. Log in with your superuser credentials

---

## Models Overview

### 1. **UserProfile** - User Health Information

**Purpose**: Stores user physical and health metrics

**Key Fields**:
- User relationship
- Height (cm), Weight (kg)
- Gender, Date of Birth
- Activity Level (Sedentary to Very Active)
- Health Goals
- Dietary Preferences
- Food Allergies
- Language Preference

**Admin Features**:
- Color-coded BMI display (Blue: Underweight, Green: Normal, Orange: Overweight, Red: Obese)
- Age calculation from date of birth
- Quick filtering by gender and activity level
- Search by username, email, or allergies

---

### 2. **HealthAssessment** - Assessment Records

**Purpose**: Stores individual health assessments with calculations

**Key Fields**:
- User reference
- Height, Weight, Age, Gender
- Activity Level, Health Goal
- Calculated: BMI, BMR, Maintenance Calories, Target Calories
- Assessment Date
- Dietary Preferences, Food Allergies

**Admin Features**:
- Color-coded BMI badge system
- Date hierarchy for easy browsing
- Quick goal visualization (⬇️ Lose Weight, ➡️ Maintain, etc.)
- Filter by BMI category and health goal
- Read-only calculated fields (BMI, BMR, etc.)

---

### 3. **MealSuggestion** - Recommended Meals

**Purpose**: Stores meal recommendations based on assessments

**Key Fields**:
- Health Assessment reference
- Meal Type (Breakfast, Lunch, Dinner, Snack)
- Name, Description
- Nutritional Info (Calories, Protein, Carbs, Fats, Fiber)
- Ingredients, Preparation Instructions, Cooking Time
- Dietary Flags (Vegetarian, Vegan, Gluten-Free, etc.)

**Admin Features**:
- Emoji-based dietary flags (🥬 Vegetarian, 🌱 Vegan, etc.)
- Quick filtering by meal type and dietary restrictions
- Search by meal name and user

---

### 4. **Conversation** - Chat Sessions

**Purpose**: Stores chat conversation records

**Key Fields**:
- User reference
- Conversation Title
- Language Used
- AI Model Used
- Creation and Update Dates
- Message Count

**Admin Features**:
- Message count display with styling
- Last message preview
- Filter by language and model
- Date hierarchy for browsing
- User username display for easy identification

---

### 5. **Message** - Individual Chat Messages

**Purpose**: Stores individual messages within conversations

**Key Fields**:
- Conversation reference
- Message Content
- Message Type (User or Assistant)
- Timestamp
- Tokens Used
- Processing Time

**Admin Features**:
- Truncated message preview (first 80 characters)
- User identification
- Timestamp in formatted display
- Date hierarchy for browsing
- Filter by message type

---

### 6. **UsageTracking** ⭐ (New)

**Purpose**: Analytics - Tracks every user action for engagement metrics

**Features**:
- Records 11 different feature types:
  - Health Assessment completion
  - Chat interactions
  - Assessment viewing
  - Profile updates
  - Meal viewing/favoriting
  - OCR usage
  - Article viewing
  - Login/Logout events

**Key Fields**:
- User
- Feature Type
- Description
- IP Address (geolocation tracking)
- User Agent (device info)
- Session ID
- Request Path
- Response Time (performance metrics)
- Timestamp

**Admin Features**:
- **List Display**: Color-coded feature badges
  - Blue: Health Assessment
  - Green: Chat
  - Purple: View Assessment
  - Orange: Profile Update
  - Pink: View Meals
  - Cyan: Login
  - Gray: Logout

- **Filtering Options**:
  - By feature type
  - By date range
  - Date hierarchy

- **Search Capabilities**:
  - Search by username
  - Search by feature type
  - Search by request path

- **Read-Only**: Usage tracking data cannot be manually added (auto-generated)

**Typical Queries You Can Run**:

```python
# View all logins in last 7 days
from django.utils import timezone
from datetime import timedelta
from core.models import UsageTracking

week_ago = timezone.now() - timedelta(days=7)
logins = UsageTracking.objects.filter(
    feature='login',
    timestamp__gte=week_ago
).order_by('-timestamp')

# Most active users
active_users = UsageTracking.objects.values('user').annotate(
    count=Count('id')
).order_by('-count')[:10]

# Feature usage distribution
feature_usage = UsageTracking.objects.values('feature').annotate(
    count=Count('id')
).order_by('-count')
```

---

### 7. **UserStats** ⭐ (New)

**Purpose**: Aggregated engagement metrics per user

**Key Metrics Tracked**:
- **Activity Counts**:
  - Total Assessments
  - Total Chat Messages
  - Total Favorite Meals
  - Total Usage Count

- **Engagement Tracking**:
  - Days Active
  - Last Active (timestamp)
  - Is Active User (activity in last 30 days)
  - Profile Completion Percentage (0-100%)

- **Last Activities**:
  - Last Assessment Date
  - Last Chat Date

**Admin Features**:
- Visual engagement status (✓ Active / ✗ Inactive)
- Progress bar for profile completion percentage
- Color-coded completion (Green ≥80%, Orange ≥50%, Red <50%)
- Read-only statistics (auto-calculated)
- Cannot be manually added (auto-created per user)

**Example Dashboard Metrics**:
- "User John has completed 12 assessments with 87% profile completion"
- "User Sarah is active (activity in last 30 days)"
- "User Mike has had 45 chat messages with 64% profile completion"

---

### 8. **ProgressTracking** - Daily Progress Records

**Purpose**: Stores daily wellness metrics

**Key Fields**:
- User, Date
- Physical: Weight, BMI, Calories Consumed/Burned, Water Intake, Steps, Workout Minutes
- Wellness: Mood Level (1-10), Energy Level (1-10)
- Notes

**Admin Features**:
- Emoji mood display (😢 to 😆)
- Color-coded energy levels (Red: Low, Orange: Medium, Green: High)
- Date hierarchy for browsing
- Filter by mood and energy levels

---

### 9. **FavoriteMeal** - Bookmarked Recipes

**Purpose**: Tracks user's favorite meals

**Key Fields**:
- User, Meal Suggestion reference
- Rating (1-5 stars)
- Personal Notes
- Added Date

**Admin Features**:
- Star rating display (⭐ visualization)
- Filter by rating and date
- Search by user and meal name

---

### 10. **NutritionArticle** - Educational Content

**Purpose**: Stores nutrition/health articles

**Key Fields**:
- Title, Slug (URL-friendly), Category
- Summary, Full Content, Image
- Author, Publication Status
- SEO Fields (Meta Description, Keywords)
- Read Time, Published Date

**Admin Features**:
- Status badge (✓ Published / ✗ Draft)
- Auto-slug generation from title
- Filter by category and status
- Date hierarchy
- Detailed SEO metadata management

---

## Usage Tracking

### How Usage Tracking Works

The system automatically tracks when users:
1. **Log in/out**: Track authentication
2. **Complete assessments**: Track health metrics submissions
3. **Use chat**: Track AI interactions
4. **Update profiles**: Track profile modifications
5. **View assessments**: Track data access
6. **View meals**: Track recipe viewing
7. **Use OCR**: Track image processing features

### Viewing Usage Analytics

**Via Admin Panel**:
1. Go to Admin → Core → Usage Tracking
2. View all tracked activities
3. Filter by feature type (e.g., "chat", "health_assessment")
4. Filter by date range using date picker
5. Search for specific users or features

**Example Filter Scenarios**:

- **Find all health assessments from January**:
  - Click "Feature" filter → Select "Health Assessment"
  - Click calendar icon next to "Timestamp" → Select January
  - View all assessments from that month

- **Find specific user activity**:
  - Use the search box, type username
  - See all activities by that user

- **Track system performance**:
  - View "Response Time" column to see which features are slow
  - Identify performance bottlenecks

---

## User Statistics

### Automatic Stat Calculation

When a user registers, `UserStats` record is automatically created and tracks:

```
User Registration
    ↓
Auto-create UserStats
    ↓
Track Activities (via UsageTracking)
    ↓
Auto-update UserStats aggregates
    ↓
Display in Admin Dashboard
```

### Interpreting User Stats

**Profile Completion**: 
- Shows what % of profile fields are filled
- 0-50%: Red (Incomplete)
- 50-80%: Orange (Mostly Complete)
- 80-100%: Green (Complete)

**Active User Status**:
- ✓ Active: Had activity in last 30 days
- ✗ Inactive: No activity in last 30 days

**Days Active**:
- Calculated as: Days since first login with any activity

---

## Admin Features

### Search & Filtering

Each model admin page provides:
- **Search Fields**: Quick text search (e.g., search for username)
- **Filters**: Category filters on the right (e.g., by BMI category, activity level)
- **Date Hierarchy**: Calendar-style browsing (year → month → date)

### Display Customization

Admin pages show relevant information:
- **Color Coding**: Visual indicators (BMI categories, status, energy levels)
- **Emoji Indicators**: Quick visual references (mood, dietary flags)
- **Calculated Fields**: Auto-computed values (BMI, BMR, profile %)

### Read-Only Fields

Some fields are read-only (cannot be edited):
- **HealthAssessment**: BMI, BMI Category, BMR (calculated)
- **UsageTracking**: All fields (auto-tracked)
- **UserStats**: All statistics (auto-calculated)
- **Message**: Timestamps (immutable)

---

## Performance Tips

### Database Queries
The admin interface is optimized with:
- **Indexes on key fields**: User, Timestamp, Feature Type
- **Efficient filtering**: Pre-filtered querysets
- **Date Hierarchy**: Faster date range queries

### Monitoring

**To check system health**:
```bash
python3 manage.py check
```

**To view database size** (SQLite):
```bash
ls -lh db.sqlite3
```

**To optimize database**:
```bash
python3 manage.py optimize_database
```

---

## Best Practices

1. **Regular Backup**: 
   - Backup `db.sqlite3` regularly
   - Keep migrations committed to version control

2. **User Privacy**:
   - Only superusers can see sensitive data
   - Consider what IP/User-Agent data to retain

3. **Data Analysis**:
   - Use Django shell to analyze patterns
   - Export reports for stakeholder review

4. **Performance**:
   - Archive old UsageTracking records if database gets too large
   - Use date filters to limit displayed records

---

## Example Django Shell Queries

```python
# Open Django shell
python3 manage.py shell

# Get user stats
from core.models import UserStats
stats = UserStats.objects.filter(is_active_user=True)
print(f"Active users: {stats.count()}")

# Find feature usage
from core.models import UsageTracking
from collections import Counter
features = UsageTracking.objects.values_list('feature', flat=True)
feature_count = Counter(features)
print(f"Most used features: {feature_count.most_common(5)}")

# Calculate engagement
from django.utils import timezone
from datetime import timedelta
this_month = timezone.now() - timedelta(days=30)
recent_users = UsageTracking.objects.filter(
    timestamp__gte=this_month
).values('user').distinct().count()
print(f"Active users this month: {recent_users}")
```

---

## Support

For issues or questions:
1. Check Django admin error messages
2. Review `manage.py check` output
3. Check application logs
4. Review migration status: `python3 manage.py showmigrations`

---

**Last Updated**: 2024
**Version**: 1.0
**Django Version**: 5.2.4+
**Python Version**: 3.10+
