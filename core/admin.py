from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q
from datetime import timedelta
from django.utils import timezone
from .models import (
    UserProfile, HealthAssessment, MealSuggestion, Conversation, Message,
    FavoriteMeal, ProgressTracking, NutritionArticle, UsageTracking, UserStats,
    EmailConfirmation, EmailLog
)

# ============================================
# USER PROFILE ADMIN
# ============================================
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'gender', 'get_bmi', 'activity_level', 'get_age', 'created_at')
    list_filter = ('gender', 'activity_level', 'created_at')
    search_fields = ('user__username', 'user__email', 'food_allergies')
    readonly_fields = ('created_at', 'updated_at', 'get_bmi_display', 'get_age_display')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Physical Metrics', {
            'fields': ('height', 'weight', 'gender', 'date_of_birth', 'get_age_display', 'get_bmi_display')
        }),
        ('Health & Activity', {
            'fields': ('activity_level', 'health_goals', 'target_weight', 'target_calories', 'water_intake_goal')
        }),
        ('Dietary Information', {
            'fields': ('diet_preference', 'dietary_preferences', 'food_allergies')
        }),
        ('Settings', {
            'fields': ('language',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_bmi(self, obj):
        bmi = obj.get_bmi()
        if bmi:
            category = obj.get_bmi_category()
            color_map = {
                'Underweight': '#3b82f6',
                'Normal weight': '#10b981',
                'Overweight': '#f59e0b',
                'Obese': '#ef4444'
            }
            color = color_map.get(category, '#64748b')
            bmi_str = f"{bmi:.1f}"
            return format_html(
                '<span style="color: {}; font-weight: bold;">{} ({})</span>',
                color, bmi_str, category
            )
        return '-'
    get_bmi.short_description = 'BMI'
    
    def get_age(self, obj):
        age = obj.age()
        return age if age else '-'
    get_age.short_description = 'Age'
    
    def get_age_display(self, obj):
        age = obj.age()
        return f"{age} years" if age else "Not calculated"
    get_age_display.short_description = 'Age'
    
    def get_bmi_display(self, obj):
        bmi = obj.get_bmi()
        category = obj.get_bmi_category()
        if bmi:
            return f"{bmi:.1f} - {category}"
        return "Not calculated"
    get_bmi_display.short_description = 'BMI'
    
    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True


# ============================================
# HEALTH ASSESSMENT ADMIN
# ============================================
@admin.register(HealthAssessment)
class HealthAssessmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_assessment_date', 'get_bmi_display', 'weight', 'get_goal')
    list_filter = ('bmi_category', 'health_goal', 'activity_level', 'assessment_date')
    search_fields = ('user__username', 'user__email', 'notes')
    readonly_fields = ('assessment_date', 'updated_at', 'bmi', 'bmr', 'bmi_category')
    date_hierarchy = 'assessment_date'
    
    fieldsets = (
        ('User & Date', {
            'fields': ('user', 'assessment_date', 'updated_at')
        }),
        ('Physical Measurements', {
            'fields': ('height', 'weight', 'age', 'gender')
        }),
        ('Health Profile', {
            'fields': ('activity_level', 'health_goal')
        }),
        ('Calculated Metrics', {
            'fields': ('bmi', 'bmi_category', 'bmr', 'maintenance_calories', 'target_calories'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('dietary_preferences', 'food_allergies', 'notes'),
            'classes': ('collapse',)
        }),
    )
    
    def get_assessment_date(self, obj):
        return obj.assessment_date.strftime('%Y-%m-%d %H:%M')
    get_assessment_date.short_description = 'Assessment Date'
    
    def get_bmi_display(self, obj):
        color_map = {
            'Underweight': '#3b82f6',
            'Normal weight': '#10b981',
            'Overweight': '#f59e0b',
            'Obese': '#ef4444'
        }
        color = color_map.get(obj.bmi_category, '#64748b')
        bmi_str = f"{obj.bmi:.1f}"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, bmi_str
        )
    get_bmi_display.short_description = 'BMI'
    
    def get_goal(self, obj):
        goal_map = {
            'weight_loss': '⬇️ Lose Weight',
            'maintain': '➡️ Maintain',
            'muscle_gain': '⬆️ Build Muscle',
            'improve_health': '❤️ Improve Health'
        }
        return goal_map.get(obj.health_goal, obj.health_goal)
    get_goal.short_description = 'Goal'
    
    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True


# ============================================
# MEAL SUGGESTION ADMIN
# ============================================
@admin.register(MealSuggestion)
class MealSuggestionAdmin(admin.ModelAdmin):
    list_display = ('name', 'meal_type', 'get_assessment_user', 'calories', 'get_dietary_flags')
    list_filter = ('meal_type', 'is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_dairy_free')
    search_fields = ('name', 'description', 'health_assessment__user__username')
    readonly_fields = ('health_assessment',)
    
    fieldsets = (
        ('Assessment', {
            'fields': ('health_assessment',)
        }),
        ('Meal Information', {
            'fields': ('meal_type', 'name', 'description')
        }),
        ('Nutritional Content', {
            'fields': ('calories', 'protein', 'carbs', 'fats', 'fiber')
        }),
        ('Preparation', {
            'fields': ('ingredients', 'preparation', 'cooking_time', 'difficulty')
        }),
        ('Dietary Flags', {
            'fields': ('is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_dairy_free', 'is_low_carb', 'is_high_protein'),
            'classes': ('collapse',)
        }),
    )
    
    def get_assessment_user(self, obj):
        return obj.health_assessment.user.username
    get_assessment_user.short_description = 'User'
    
    def get_dietary_flags(self, obj):
        flags = []
        if obj.is_vegetarian:
            flags.append('🥬')
        if obj.is_vegan:
            flags.append('🌱')
        if obj.is_gluten_free:
            flags.append('🌾')
        if obj.is_dairy_free:
            flags.append('🥛')
        if obj.is_low_carb:
            flags.append('📉')
        if obj.is_high_protein:
            flags.append('💪')
        return ' '.join(flags) if flags else '-'
    get_dietary_flags.short_description = 'Flags'
    
    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True


# ============================================
# CONVERSATION & MESSAGE ADMIN
# ============================================
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'get_message_count', 'language', 'pinned', 'get_created_date', 'updated_at')
    list_filter = ('language', 'model_used', 'pinned', 'created_at', 'updated_at')
    search_fields = ('user__username', 'title')
    readonly_fields = ('id', 'created_at', 'updated_at', 'get_message_count', 'get_last_message')
    date_hierarchy = 'created_at'
    ordering = ('-pinned', '-updated_at')
    actions = ['backfill_updated_at']
    
    fieldsets = (
        ('Conversation Info', {
            'fields': ('id', 'user', 'title')
        }),
        ('Settings', {
            'fields': ('language', 'model_used')
        }),
        ('Statistics', {
            'fields': ('get_message_count', 'get_last_message'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_message_count(self, obj):
        count = obj.get_message_count()
        return format_html('<span style="background-color: #e0e7ff; padding: 2px 8px; border-radius: 4px;">{}</span>', count)
    get_message_count.short_description = 'Messages'
    
    def get_last_message(self, obj):
        last = obj.get_last_message()
        if last:
            preview = last.message[:100] + '...' if len(last.message) > 100 else last.message
            return preview
        return '-'
    get_last_message.short_description = 'Last Message'
    
    def get_created_date(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    get_created_date.short_description = 'Created'
    
    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True

    def backfill_updated_at(self, request, queryset):
        """Admin action: set conversation.updated_at to last message timestamp if newer.
        Useful to correct sorting for existing data.
        """
        from django.db.models import Max
        updated_count = 0
        for conv in queryset:
            last_ts = conv.messages.aggregate(m=Max('timestamp'))['m']
            if last_ts and (conv.updated_at is None or last_ts > conv.updated_at):
                conv.updated_at = last_ts
                conv.save(update_fields=['updated_at'])
                updated_count += 1
        self.message_user(request, f"Updated 'updated_at' for {updated_count} conversation(s).")
    backfill_updated_at.short_description = "Backfill Updated At from last message"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('get_preview', 'message_type', 'get_conversation_user', 'get_timestamp', 'tokens_used')
    list_filter = ('message_type', 'timestamp')
    search_fields = ('message', 'conversation__user__username')
    readonly_fields = ('id', 'timestamp', 'conversation')
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Message Info', {
            'fields': ('id', 'conversation', 'message_type')
        }),
        ('Content', {
            'fields': ('message',)
        }),
        ('Metrics', {
            'fields': ('tokens_used', 'processing_time', 'timestamp'),
            'classes': ('collapse',)
        }),
    )
    
    def get_preview(self, obj):
        preview = obj.message[:80] + '...' if len(obj.message) > 80 else obj.message
        return preview
    get_preview.short_description = 'Message Preview'
    
    def get_conversation_user(self, obj):
        return obj.conversation.user.username
    get_conversation_user.short_description = 'User'
    
    def get_timestamp(self, obj):
        return obj.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    get_timestamp.short_description = 'Timestamp'
    
    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True


# ============================================
# USAGE TRACKING ADMIN
# ============================================
@admin.register(UsageTracking)
class UsageTrackingAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_feature_display', 'get_timestamp', 'get_response_time', 'request_path')
    list_filter = ('feature', 'timestamp')
    search_fields = ('user__username', 'description', 'request_path')
    readonly_fields = ('user', 'timestamp')
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('User & Time', {
            'fields': ('user', 'timestamp')
        }),
        ('Feature', {
            'fields': ('feature', 'description')
        }),
        ('Request Info', {
            'fields': ('request_path', 'session_id'),
            'classes': ('collapse',)
        }),
        ('Client Info', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Performance', {
            'fields': ('response_time',),
            'classes': ('collapse',)
        }),
    )
    
    def get_feature_display(self, obj):
        feature_colors = {
            'health_assessment': '#3b82f6',
            'chat': '#10b981',
            'view_assessment': '#8b5cf6',
            'profile_update': '#f59e0b',
            'view_meals': '#ec4899',
            'login': '#06b6d4',
            'logout': '#6b7280',
        }
        color = feature_colors.get(obj.feature, '#64748b')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            color, obj.get_feature_display()
        )
    get_feature_display.short_description = 'Feature'
    
    def get_timestamp(self, obj):
        return obj.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    get_timestamp.short_description = 'Time'
    
    def get_response_time(self, obj):
        if obj.response_time:
            return f"{obj.response_time:.2f}s"
        return '-'
    get_response_time.short_description = 'Response Time'
    
    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True


# ============================================
# USER STATS ADMIN
# ============================================
@admin.register(UserStats)
class UserStatsAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_total_usage', 'get_engagement', 'profile_completion_percentage', 'is_active_user', 'last_active')
    list_filter = ('is_active_user', 'last_active')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'get_engagement_chart')
    
    fieldsets = (
        ('User', {
            'fields': ('user', 'is_active_user')
        }),
        ('Activity Counts', {
            'fields': ('total_assessments', 'total_chat_messages', 'total_favorite_meals', 'total_usage_count')
        }),
        ('Engagement', {
            'fields': ('days_active', 'last_active', 'profile_completion_percentage', 'get_engagement_chart'),
            'classes': ('collapse',)
        }),
        ('Last Activities', {
            'fields': ('last_assessment_date', 'last_chat_date'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_total_usage(self, obj):
        return format_html(
            '<span style="background-color: #e0e7ff; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            obj.total_usage_count
        )
    get_total_usage.short_description = 'Total Usage'
    
    def get_engagement(self, obj):
        if obj.is_active_user:
            return format_html('<span style="color: #10b981; font-weight: bold;">✓ Active</span>')
        return format_html('<span style="color: #ef4444; font-weight: bold;">✗ Inactive</span>')
    get_engagement.short_description = 'Status'
    
    def get_engagement_chart(self, obj):
        percentage = obj.profile_completion_percentage
        color = '#10b981' if percentage >= 80 else '#f59e0b' if percentage >= 50 else '#ef4444'
        return format_html(
            '<div style="background-color: #e5e7eb; border-radius: 4px; overflow: hidden; width: 200px; height: 20px;">'
            '<div style="background-color: {}; width: {}%; height: 100%; transition: width 0.3s;"></div>'
            '</div>'
            '<p style="margin-top: 8px;">{}%</p>',
            color, percentage, percentage
        )
    get_engagement_chart.short_description = 'Profile Completion'
    
    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True


# ============================================
# PROGRESS TRACKING ADMIN
# ============================================
@admin.register(ProgressTracking)
class ProgressTrackingAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'weight', 'get_mood_display', 'get_energy_display', 'created_at')
    list_filter = ('date', 'mood_level', 'energy_level')
    search_fields = ('user__username', 'notes')
    readonly_fields = ('created_at',)
    date_hierarchy = 'date'
    
    fieldsets = (
        ('User & Date', {
            'fields': ('user', 'date')
        }),
        ('Physical Metrics', {
            'fields': ('weight', 'bmi', 'calories_consumed', 'calories_burned', 'water_intake', 'steps', 'workout_minutes')
        }),
        ('Wellness Metrics', {
            'fields': ('mood_level', 'energy_level')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_mood_display(self, obj):
        if obj.mood_level:
            emojis = ['😢', '😞', '😐', '🙂', '😊', '😄', '😆', '😃', '🤩', '🎉']
            emoji = emojis[obj.mood_level - 1] if 1 <= obj.mood_level <= 10 else '😐'
            return format_html('{} ({})', emoji, obj.mood_level)
        return '-'
    get_mood_display.short_description = 'Mood'
    
    def get_energy_display(self, obj):
        if obj.energy_level:
            if obj.energy_level <= 3:
                color = '#ef4444'
                status = 'Low'
            elif obj.energy_level <= 6:
                color = '#f59e0b'
                status = 'Medium'
            else:
                color = '#10b981'
                status = 'High'
            return format_html('<span style="color: {}; font-weight: bold;">{} ({})</span>', color, status, obj.energy_level)
        return '-'
    get_energy_display.short_description = 'Energy'
    
    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True


# ============================================
# FAVORITE MEAL ADMIN
# ============================================
@admin.register(FavoriteMeal)
class FavoriteMealAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_meal_name', 'get_rating_display', 'added_date')
    list_filter = ('rating', 'added_date')
    search_fields = ('user__username', 'meal_suggestion__name')
    readonly_fields = ('added_date', 'user', 'meal_suggestion')
    date_hierarchy = 'added_date'
    
    fieldsets = (
        ('Favorite Info', {
            'fields': ('user', 'meal_suggestion')
        }),
        ('Rating & Notes', {
            'fields': ('rating', 'notes')
        }),
        ('Added Date', {
            'fields': ('added_date',),
            'classes': ('collapse',)
        }),
    )
    
    def get_meal_name(self, obj):
        return obj.meal_suggestion.name
    get_meal_name.short_description = 'Meal'
    
    def get_rating_display(self, obj):
        if obj.rating:
            stars = '⭐' * obj.rating
            return format_html('<span style="font-size: 1.2em;">{}</span> ({})', stars, obj.rating)
        return '-'
    get_rating_display.short_description = 'Rating'
    
    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True


# ============================================
# NUTRITION ARTICLE ADMIN
# ============================================
@admin.register(NutritionArticle)
class NutritionArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'get_status', 'get_published_date', 'read_time')
    list_filter = ('category', 'is_published', 'published_date')
    search_fields = ('title', 'content', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('published_date',)
    date_hierarchy = 'published_date'
    
    fieldsets = (
        ('Article Info', {
            'fields': ('title', 'slug', 'category', 'author')
        }),
        ('Content', {
            'fields': ('summary', 'content', 'image_url')
        }),
        ('SEO', {
            'fields': ('meta_description', 'keywords'),
            'classes': ('collapse',)
        }),
        ('Publishing', {
            'fields': ('is_published', 'published_date', 'read_time'),
            'classes': ('collapse',)
        }),
    )
    
    def get_status(self, obj):
        if obj.is_published:
            return format_html('<span style="color: #10b981; font-weight: bold;">✓ Published</span>')
        return format_html('<span style="color: #f59e0b; font-weight: bold;">✗ Draft</span>')
    get_status.short_description = 'Status'
    
    def get_published_date(self, obj):
        return obj.published_date.strftime('%Y-%m-%d %H:%M')
    get_published_date.short_description = 'Published'
    
    def has_add_permission(self, request):
        return True
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True


# ============================================
# EMAIL CONFIRMATION ADMIN
# ============================================
@admin.register(EmailConfirmation)
class EmailConfirmationAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_status', 'get_expiry_status', 'get_created_date', 'confirmed_at')
    list_filter = ('is_confirmed', 'created_at')
    search_fields = ('user__username', 'user__email', 'token')
    readonly_fields = ('token', 'created_at', 'confirmed_at', 'user')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'token')
        }),
        ('Confirmation Status', {
            'fields': ('is_confirmed', 'created_at', 'confirmed_at')
        }),
    )
    
    def get_status(self, obj):
        if obj.is_confirmed:
            return format_html('<span style="color: #10b981; font-weight: bold;">✓ Confirmed</span>')
        return format_html('<span style="color: #ef4444; font-weight: bold;">✗ Pending</span>')
    get_status.short_description = 'Status'
    
    def get_expiry_status(self, obj):
        if obj.is_confirmed:
            return format_html('<span style="color: #10b981;">Confirmed</span>')
        if obj.is_expired():
            return format_html('<span style="color: #ef4444; font-weight: bold;">Expired</span>')
        return format_html('<span style="color: #f59e0b;">Active</span>')
    get_expiry_status.short_description = 'Expiry Status'
    
    def get_created_date(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    get_created_date.short_description = 'Created'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return True


# ============================================
# EMAIL LOG ADMIN
# ============================================
@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_email_type', 'email_address', 'get_status', 'get_sent_date')
    list_filter = ('email_type', 'is_sent', 'sent_at')
    search_fields = ('user__username', 'email_address', 'subject')
    readonly_fields = ('user', 'email_address', 'sent_at', 'subject')
    date_hierarchy = 'sent_at'
    
    fieldsets = (
        ('Email Info', {
            'fields': ('user', 'email_address', 'email_type', 'subject')
        }),
        ('Content', {
            'fields': ('message_preview',)
        }),
        ('Status', {
            'fields': ('is_sent', 'error_message', 'sent_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_email_type(self, obj):
        type_colors = {
            'confirmation': '#3b82f6',
            'welcome': '#10b981',
            'password_reset': '#f59e0b',
            'notification': '#8b5cf6',
            'other': '#64748b',
        }
        color = type_colors.get(obj.email_type, '#64748b')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            color, obj.get_email_type_display()
        )
    get_email_type.short_description = 'Type'
    
    def get_status(self, obj):
        if obj.is_sent:
            return format_html('<span style="color: #10b981; font-weight: bold;">✓ Sent</span>')
        return format_html('<span style="color: #ef4444; font-weight: bold;">✗ Failed</span>')
    get_status.short_description = 'Status'
    
    def get_sent_date(self, obj):
        return obj.sent_at.strftime('%Y-%m-%d %H:%M:%S')
    get_sent_date.short_description = 'Sent'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return True


# ============================================
# ADMIN SITE CUSTOMIZATION
# ============================================
admin.site.site_header = "FitWell Administration"
admin.site.site_title = "FitWell Admin"
admin.site.index_title = "Welcome to FitWell Admin Dashboard"
