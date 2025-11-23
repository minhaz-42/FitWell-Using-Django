"""
Utility functions for tracking user activity and engagement
"""
from .models import UsageTracking, UserStats
from django.utils import timezone
import time


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Extract user agent from request"""
    return request.META.get('HTTP_USER_AGENT', '')


def log_usage(request, feature, description='', response_time=None):
    """
    Log user activity for analytics and tracking
    
    Args:
        request: HTTP request object
        feature: Feature type (from UsageTracking.FEATURE_CHOICES)
        description: Additional description of the action
        response_time: Time taken to process the request in seconds
    """
    if request.user.is_authenticated:
        try:
            UsageTracking.objects.create(
                user=request.user,
                feature=feature,
                description=description,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                session_id=request.session.session_key,
                request_path=request.path,
                response_time=response_time
            )
        except Exception as e:
            print(f"Error logging usage: {e}")


def update_user_stats(user):
    """
    Update user statistics based on activity
    
    Args:
        user: Django User object
    """
    try:
        from .models import HealthAssessment, Conversation, FavoriteMeal, UserProfile
        
        stats = UserStats.objects.get(user=user)
        
        # Count assessments
        stats.total_assessments = HealthAssessment.objects.filter(user=user).count()
        
        # Count messages
        total_messages = 0
        for conversation in Conversation.objects.filter(user=user):
            total_messages += conversation.get_message_count()
        stats.total_chat_messages = total_messages
        
        # Count favorite meals
        stats.total_favorite_meals = FavoriteMeal.objects.filter(user=user).count()
        
        # Update engagement metrics
        usage_count = UsageTracking.objects.filter(user=user).count()
        stats.total_usage_count = usage_count
        
        # Check last activities
        last_assessment = HealthAssessment.objects.filter(user=user).order_by('-assessment_date').first()
        if last_assessment:
            stats.last_assessment_date = last_assessment.assessment_date
        
        last_conversation = Conversation.objects.filter(user=user).order_by('-updated_at').first()
        if last_conversation:
            stats.last_chat_date = last_conversation.updated_at
        
        # Update last active
        stats.last_active = timezone.now()
        
        # Check if user is active (had activity in last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_activity = UsageTracking.objects.filter(
            user=user,
            timestamp__gte=thirty_days_ago
        ).count()
        stats.is_active_user = recent_activity > 0
        
        # Calculate profile completion percentage
        profile = UserProfile.objects.get(user=user)
        completion = 0
        total_fields = 0
        
        fields_to_check = [
            'height', 'weight', 'gender', 'date_of_birth', 'activity_level',
            'diet_preference', 'dietary_preferences', 'food_allergies'
        ]
        
        for field in fields_to_check:
            total_fields += 1
            value = getattr(profile, field, None)
            if value and value != '':
                completion += 1
        
        # Also check user info
        total_fields += 2  # first_name, last_name
        if user.first_name:
            completion += 1
        if user.last_name:
            completion += 1
        
        stats.profile_completion_percentage = int((completion / total_fields) * 100) if total_fields > 0 else 0
        
        stats.save()
    except Exception as e:
        print(f"Error updating user stats: {e}")


def track_view_execution(feature, description=''):
    """
    Decorator to automatically track view execution
    
    Usage:
        @track_view_execution('health_assessment', 'User submitted health assessment')
        def health_assessment_view(request):
            ...
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            start_time = time.time()
            try:
                response = view_func(request, *args, **kwargs)
                response_time = time.time() - start_time
                log_usage(request, feature, description, response_time)
                update_user_stats(request.user)
                return response
            except Exception as e:
                response_time = time.time() - start_time
                log_usage(request, feature, f"{description} - Error: {str(e)}", response_time)
                raise
        return wrapper
    return decorator
