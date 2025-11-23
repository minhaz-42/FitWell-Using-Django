# 🚀 NutriAI Admin Setup - Quick Reference Card

## ⚡ 30-Second Quick Start

```bash
# 1. Create superuser (one-time)
cd /Users/tanvir/Desktop/nutriaiproject
python3 manage.py createsuperuser
# Enter username, email, password when prompted

# 2. Start the server
python3 manage.py runserver

# 3. Visit in browser
# http://localhost:8000/admin/

# 4. Log in with superuser credentials
```

---

## 📊 What You Can Do Now

### 1. **Track User Activity** 📱
   - Go to: Admin → Core → **Usage Tracking**
   - See all logins, assessments, profile updates
   - Filter by feature type or date
   - View IP addresses and response times

### 2. **View User Engagement** 👥
   - Go to: Admin → Core → **User Stats**
   - See active users vs inactive
   - Check profile completion %
   - View engagement metrics

### 3. **Analyze Health Data** 💪
   - Go to: Admin → Core → **Health Assessment**
   - Color-coded BMI display
   - Filter by BMI category or health goal
   - View trends over time

### 4. **Manage Content** 📝
   - Admin → Core → **Meal Suggestion**
   - Admin → Core → **Nutrition Article**
   - Admin → Core → **Conversation**

---

## 🎯 Common Admin Tasks

### See Who Logged In Today
1. Go to: Admin → Core → Usage Tracking
2. Click the date column header to filter
3. Select "Today"
4. Filter feature = "login"

### Find Most Active User
1. Go to: Admin → Core → User Stats
2. Click "Is Active User" filter → "Yes"
3. Sort by "Total Usage" (click column)

### View Specific User's Activity
1. Go to: Admin → Core → Usage Tracking
2. In search box, type username
3. See all their activities with timestamps

### Check System Performance
1. Go to: Admin → Core → Usage Tracking
2. Scroll right to "Response Time" column
3. Slow requests show high response times
4. Identify which features need optimization

---

## 🔍 Filter & Search Cheat Sheet

### By Feature Type
- Health Assessment
- Chat
- Profile Update
- Login/Logout
- View Assessment
- View Meals
- (and 5 more)

### By Date
- Click column header for sorting
- Use date picker for range selection
- Date hierarchy for year → month → day

### By User
- Search box: Type username
- View all activities by that user

### By Status
- Active User: Yes/No
- Published: Yes/No
- BMI Category: Underweight/Normal/Overweight/Obese

---

## 📈 Key Metrics to Monitor

| Metric | Location | What It Means |
|--------|----------|---------------|
| Usage Count | UserStats | Total user interactions |
| Active User | UserStats | Activity in last 30 days |
| Profile % | UserStats | How complete profile is |
| Response Time | UsageTracking | System performance |
| Feature Usage | UsageTracking | Which features most used |
| Last Active | UserStats | When user last used app |

---

## ⚙️ Admin Features Cheat Sheet

### UserProfile Admin
- **Look for**: Color-coded BMI (🔵 Normal, 🟢 Green, 🟠 Orange, 🔴 Red)
- **Search**: Username, email, allergies
- **Filter**: Gender, activity level, date

### HealthAssessment Admin
- **Look for**: BMI badges, health goal icons
- **Filter**: BMI category, health goal
- **View**: Calculated metrics (BMR, calories, etc.)

### UsageTracking Admin (🌟 NEW)
- **Feature badges**: 7 different colors for feature types
- **IP tracking**: Geolocation info available
- **Response time**: Performance monitoring
- **Read-only**: Can't accidentally modify tracking data

### UserStats Admin (🌟 NEW)
- **Active indicator**: ✓ Active / ✗ Inactive
- **Completion bar**: Visual progress (Green ≥80%, Orange ≥50%, Red <50%)
- **Auto-updated**: Stats update as users interact
- **Read-only**: Auto-calculated metrics

---

## 🛑 Common Questions

**Q: How do I know if tracking is working?**
A: Log in with a test account, perform an action (view profile, do assessment), then check Admin → Usage Tracking. You should see new records.

**Q: Where is the user's password stored?**
A: Django handles user passwords in the auth_user table. Never visible in admin. Click "Users" to manage them.

**Q: Can I delete usage tracking data?**
A: It's read-only by design (prevents accidents). For data cleanup, use Django shell:
```python
from core.models import UsageTracking
UsageTracking.objects.filter(timestamp__lt=old_date).delete()
```

**Q: How often do stats update?**
A: UserStats updates whenever user interacts with tracked features. Updates are automatic.

**Q: Can regular users see the admin panel?**
A: No, only superusers can access `/admin/`. Regular users cannot log in.

---

## 📚 Documentation Files

For more details, see:
1. **ADMIN_TRACKING_GUIDE.md** - Comprehensive 500+ line guide
2. **ADMIN_IMPLEMENTATION_COMPLETE.md** - What was built and why
3. **CHANGES_MADE.md** - Technical details of all changes

---

## ✅ System Health Check

Run this to verify everything works:
```bash
cd /Users/tanvir/Desktop/nutriaiproject
python3 manage.py check
```

Should show: **"System check identified no issues (0 silenced)."** ✅

---

## 🎨 Admin Interface Features

✨ **Color Coding**:
- Blue (#3b82f6): Underweight, Health Assessment
- Green (#10b981): Normal Weight, Active, Published
- Orange (#f59e0b): Overweight, Medium priority
- Red (#ef4444): Obese, Inactive, Overweight

😊 **Emoji Indicators**:
- 💪 Dietary flags (vegetarian, vegan, gluten-free, etc.)
- ⭐ Star ratings
- ✓/✗ Status indicators
- 📊 Progress bars

---

## 🔐 Security Reminder

- **Keep superuser password safe**: Only share with admins
- **Change SECRET_KEY for production**: See settings.py
- **Enable SSL for production**: Use HTTPS
- **Regular backups**: Backup db.sqlite3 frequently

---

## 🚨 Troubleshooting

**Issue**: Can't access admin
→ Solution: Verify superuser created: `python3 manage.py createsuperuser`

**Issue**: No usage data showing
→ Solution: Data only logged for authenticated users. Log in and perform actions.

**Issue**: Stats show all zeros
→ Solution: Stats auto-update after user actions. Perform assessment, chat, or profile update.

**Issue**: Server won't start
→ Solution: Run `python3 manage.py check` to see errors

---

## 📋 Tracked Events Reference

```
✓ Login          → log_usage('login')
✓ Logout         → log_usage('logout')
✓ Assessment     → log_usage('health_assessment')
✓ Profile View   → log_usage('view_profile')
✓ Profile Update → log_usage('profile_update')
```

More coming: Chat, meals, articles, OCR, favorites

---

**Ready to go!** 🚀

Visit: `http://localhost:8000/admin/`

Username: Your superuser username
Password: Your superuser password

---

**Version**: 1.0
**Last Updated**: 2024
**Status**: ✅ Ready to Use
