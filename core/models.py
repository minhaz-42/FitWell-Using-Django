from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid


def _generate_uuid_str():
    return str(uuid.uuid4())

class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('P', 'Prefer not to say'),
    ]
    
    ACTIVITY_LEVEL_CHOICES = [
        ('sedentary', 'Sedentary (little or no exercise)'),
        ('light', 'Lightly active (light exercise 1-3 days/week)'),
        ('moderate', 'Moderately active (moderate exercise 3-5 days/week)'),
        ('active', 'Very active (hard exercise 6-7 days/week)'),
        ('very_active', 'Extremely active (very hard exercise & physical job)'),
    ]
    
    DIET_PREFERENCE_CHOICES = [
        ('none', 'No specific diet'),
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('pescatarian', 'Pescatarian'),
        ('keto', 'Keto'),
        ('paleo', 'Paleo'),
        ('mediterranean', 'Mediterranean'),
        ('low_carb', 'Low Carb'),
        ('gluten_free', 'Gluten Free'),
        ('dairy_free', 'Dairy Free'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('bn', 'Bengali'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    height = models.FloatField(
        help_text="Height in cm", 
        null=True, 
        blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(250)]
    )
    weight = models.FloatField(
        help_text="Weight in kg", 
        null=True, 
        blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(300)]
    )
    activity_level = models.CharField(max_length=20, choices=ACTIVITY_LEVEL_CHOICES, default='sedentary')
    diet_preference = models.CharField(max_length=20, choices=DIET_PREFERENCE_CHOICES, default='none')
    dietary_preferences = models.TextField(blank=True, help_text="Any dietary restrictions or preferences")
    food_allergies = models.TextField(blank=True, help_text="List any food allergies")
    health_goals = models.TextField(blank=True, help_text="Your health and nutrition goals")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Health metrics tracking
    target_weight = models.FloatField(null=True, blank=True)
    target_calories = models.IntegerField(null=True, blank=True)
    water_intake_goal = models.FloatField(default=2.0, help_text="Daily water intake goal in liters")
    
    # Language preference for chat
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['activity_level']),
        ]

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    def get_bmi(self):
        if self.height and self.weight:
            from .utils import calculate_bmi
            return calculate_bmi(self.height, self.weight)
        return None
    
    def get_bmi_category(self):
        bmi = self.get_bmi()
        if bmi:
            from .utils import get_bmi_category
            return get_bmi_category(bmi)
        return "Unknown"

class Conversation(models.Model):
    # Store UUID as text to keep SQLite compatibility and avoid type binding issues
    id = models.CharField(primary_key=True, max_length=36, default=_generate_uuid_str, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255, default="New Conversation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Conversation metadata
    language = models.CharField(max_length=2, choices=UserProfile.LANGUAGE_CHOICES, default='en')
    model_used = models.CharField(max_length=50, default='nutrition', help_text="AI model used for this conversation")
    # Pin conversations for quick access
    pinned = models.BooleanField(default=False, help_text="Pin conversation to top of sidebar")
    # Track when the user last read this conversation (for unread counts)
    last_read_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when user last read this conversation")
    
    class Meta:
        ordering = ['-pinned', '-updated_at']
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
    
    def __str__(self):
        return f"{self.user.username} - {self.title} - {self.updated_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_message_count(self):
        return self.messages.count()
    
    def get_last_message(self):
        return self.messages.order_by('-timestamp').first()

class Message(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    message = models.TextField()
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Message metadata
    tokens_used = models.IntegerField(null=True, blank=True, help_text="Number of tokens used in this message")
    processing_time = models.FloatField(null=True, blank=True, help_text="Processing time in seconds")
    
    class Meta:
        ordering = ['timestamp']
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
        ]
    
    def __str__(self):
        message_preview = self.message[:50] + "..." if len(self.message) > 50 else self.message
        return f"{self.message_type}: {message_preview}"

class HealthAssessment(models.Model):
    GOAL_CHOICES = [
        ('weight_loss', 'Lose Weight'),
        ('maintain', 'Maintain Weight'),
        ('muscle_gain', 'Build Muscle'),
        ('improve_health', 'Improve Overall Health'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='health_assessments')
    height = models.FloatField(validators=[MinValueValidator(50), MaxValueValidator(250)])
    weight = models.FloatField(validators=[MinValueValidator(20), MaxValueValidator(300)])
    age = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(120)], null=True, blank=True)
    gender = models.CharField(max_length=1, choices=UserProfile.GENDER_CHOICES)
    activity_level = models.CharField(max_length=20, choices=UserProfile.ACTIVITY_LEVEL_CHOICES)
    health_goal = models.CharField(max_length=20, choices=GOAL_CHOICES)
    
    # Calculated fields
    bmi = models.FloatField()
    bmi_category = models.CharField(max_length=50)
    bmr = models.FloatField(help_text="Basal Metabolic Rate")
    maintenance_calories = models.IntegerField(help_text="Daily maintenance calories")
    target_calories = models.IntegerField(help_text="Recommended daily calorie target")
    
    # Additional info
    dietary_preferences = models.TextField(blank=True)
    food_allergies = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Timestamps
    assessment_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-assessment_date']
        verbose_name = "Health Assessment"
        verbose_name_plural = "Health Assessments"
        indexes = [
            models.Index(fields=['user', '-assessment_date']),
            models.Index(fields=['bmi_category']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.assessment_date.strftime('%Y-%m-%d')} - BMI: {self.bmi:.1f}"

class MealSuggestion(models.Model):
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('morning_snack', 'Morning Snack'),
        ('lunch', 'Lunch'),
        ('afternoon_snack', 'Afternoon Snack'),
        ('dinner', 'Dinner'),
        ('evening_snack', 'Evening Snack'),
    ]
    
    health_assessment = models.ForeignKey(
        HealthAssessment, 
        on_delete=models.CASCADE, 
        related_name='meal_suggestions'
    )
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    name = models.CharField(max_length=200)
    description = models.TextField()
    calories = models.IntegerField()
    protein = models.FloatField(help_text="Protein in grams")
    carbs = models.FloatField(help_text="Carbohydrates in grams")
    fats = models.FloatField(help_text="Fats in grams")
    fiber = models.FloatField(help_text="Fiber in grams", default=0)
    ingredients = models.TextField()
    preparation = models.TextField(blank=True)
    cooking_time = models.IntegerField(help_text="Cooking time in minutes", default=15)
    difficulty = models.CharField(
        max_length=10,
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard'),
        ],
        default='easy'
    )
    
    # Nutritional flags
    is_vegetarian = models.BooleanField(default=False)
    is_vegan = models.BooleanField(default=False)
    is_gluten_free = models.BooleanField(default=False)
    is_dairy_free = models.BooleanField(default=False)
    is_low_carb = models.BooleanField(default=False)
    is_high_protein = models.BooleanField(default=False)

    class Meta:
        ordering = ['meal_type']
        verbose_name = "Meal Suggestion"
        verbose_name_plural = "Meal Suggestions"

    def __str__(self):
        return f"{self.meal_type}: {self.name}"

class ProgressTracking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress_entries')
    date = models.DateField(default=timezone.now)
    weight = models.FloatField(
        validators=[MinValueValidator(20), MaxValueValidator(300)],
        null=True,
        blank=True
    )
    bmi = models.FloatField(null=True, blank=True)
    calories_consumed = models.IntegerField(null=True, blank=True)
    calories_burned = models.IntegerField(null=True, blank=True)
    water_intake = models.FloatField(help_text="Water intake in liters", null=True, blank=True)
    steps = models.IntegerField(null=True, blank=True)
    workout_minutes = models.IntegerField(null=True, blank=True)
    
    # Mood and energy levels (1-10 scale)
    mood_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True,
        blank=True
    )
    energy_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True,
        blank=True
    )
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
        verbose_name = "Progress Tracking"
        verbose_name_plural = "Progress Tracking"
        indexes = [
            models.Index(fields=['user', '-date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.date}"

class FavoriteMeal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_meals')
    meal_suggestion = models.ForeignKey(MealSuggestion, on_delete=models.CASCADE)
    added_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    # Rating (1-5 stars)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ['user', 'meal_suggestion']
        verbose_name = "Favorite Meal"
        verbose_name_plural = "Favorite Meals"

    def __str__(self):
        return f"{self.user.username} - {self.meal_suggestion.name}"

class NutritionArticle(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General Nutrition'),
        ('weight_loss', 'Weight Loss'),
        ('muscle_gain', 'Muscle Gain'),
        ('healthy_eating', 'Healthy Eating'),
        ('sports_nutrition', 'Sports Nutrition'),
        ('diet_plans', 'Diet Plans'),
        ('recipes', 'Recipes'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    summary = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    author = models.CharField(max_length=100, blank=True)
    published_date = models.DateTimeField(default=timezone.now)
    is_published = models.BooleanField(default=True)
    
    # SEO and metadata
    slug = models.SlugField(unique=True, max_length=200)
    meta_description = models.TextField(blank=True)
    keywords = models.TextField(blank=True)
    
    # Media
    image_url = models.URLField(blank=True)
    read_time = models.IntegerField(help_text="Estimated reading time in minutes", default=5)

    class Meta:
        ordering = ['-published_date']
        verbose_name = "Nutrition Article"
        verbose_name_plural = "Nutrition Articles"

    def __str__(self):
        return self.title


class UsageTracking(models.Model):
    """Track user activity and usage patterns"""
    FEATURE_CHOICES = [
        ('health_assessment', 'Health Assessment'),
        ('chat', 'Chat Assistant'),
        ('view_assessment', 'View Assessment'),
        ('profile_update', 'Profile Update'),
        ('view_meals', 'View Meal Suggestions'),
        ('favorite_meal', 'Favorite Meal'),
        ('progress_tracking', 'Progress Tracking'),
        ('ocr', 'OCR Feature'),
        ('article_view', 'Article View'),
        ('login', 'Login'),
        ('logout', 'Logout'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usage_tracking')
    feature = models.CharField(max_length=50, choices=FEATURE_CHOICES)
    description = models.TextField(blank=True, help_text="Additional details about the action")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, help_text="Browser/client information")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Session/Request tracking
    session_id = models.CharField(max_length=255, blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    
    # Performance metrics
    response_time = models.FloatField(null=True, blank=True, help_text="Response time in seconds")
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Usage Tracking"
        verbose_name_plural = "Usage Tracking"
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['feature', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.feature} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class UserStats(models.Model):
    """Aggregate statistics for users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='stats')
    total_assessments = models.IntegerField(default=0)
    total_chat_messages = models.IntegerField(default=0)
    total_favorite_meals = models.IntegerField(default=0)
    last_assessment_date = models.DateTimeField(null=True, blank=True)
    last_chat_date = models.DateTimeField(null=True, blank=True)
    profile_completion_percentage = models.IntegerField(default=0, help_text="0-100 percentage")
    total_usage_count = models.IntegerField(default=0)
    
    # Engagement metrics
    days_active = models.IntegerField(default=0)
    last_active = models.DateTimeField(auto_now=True)
    is_active_user = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Stats"
        verbose_name_plural = "User Stats"
    
    def __str__(self):
        return f"{self.user.username}'s Statistics"


# Signal to create UserStats when user is created
@receiver(post_save, sender=User)
def create_user_stats(sender, instance, created, **kwargs):
    if created:
        UserStats.objects.create(user=instance)

# Signal to create user profile when user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()