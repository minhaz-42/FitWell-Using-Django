from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.utils.decorators import method_decorator
from django import forms
from django.contrib.auth.models import User
import json
from django.db import transaction
from django.utils import timezone
from .models import (
    UserProfile, HealthAssessment, MealSuggestion, Conversation, Message,
    FavoriteMeal
)
from .utils import (
    calculate_bmi, 
    get_bmi_category, 
    generate_meal_suggestions,
    get_calorie_recommendation,
    get_health_tips,
    validate_health_data
)
from .tracking_utils import log_usage, update_user_stats


# ============================================
# CUSTOM REGISTRATION FORM WITH EMAIL
# ============================================
class CustomUserCreationForm(UserCreationForm):
    """Custom registration form with email field"""
    email = forms.EmailField(
        required=True,
        label='Email Address',
        help_text='',
        widget=forms.EmailInput(attrs={
            'placeholder': 'your@email.com',
            'class': 'form-input',
        })
    )
    
    username = forms.CharField(
        max_length=150,
        label='Username',
        help_text='',
        widget=forms.TextInput(attrs={
            'placeholder': 'Choose a username',
            'class': 'form-input',
        })
    )
    
    password1 = forms.CharField(
        label='Password',
        help_text='',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter password',
            'class': 'form-input',
        })
    )
    
    password2 = forms.CharField(
        label='Confirm Password',
        help_text='',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm password',
            'class': 'form-input',
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def clean_email(self):
        """Validate email is unique"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email
    
    def clean_password2(self):
        """Validate passwords match and meet requirements"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('Passwords do not match.')
            if len(password1) < 8:
                raise forms.ValidationError('Password must be at least 8 characters long.')
        
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


# ============================================
# VIEWS
# ============================================

def home(request):
    """Home page view"""
    return render(request, 'core/home.html')

@csrf_protect
def register_view(request):
    """User registration view

    Users are created as active and a welcome email is sent immediately.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Activate user immediately for local development
            user.is_active = True
            user.save()

            # Send welcome/thank you email
            from .email_utils import send_welcome_email
            try:
                sent = send_welcome_email(user)
                if sent:
                    print(f"\n✓ Welcome email sent to: {user.email}")
                else:
                    print(f"Warning: welcome email not sent for: {user.email}")
            except Exception as e:
                print(f"Error sending welcome email: {e}")

            messages.success(
                request,
                'Registration successful! Your account has been created. You can now log in.'
            )

            return redirect('login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is None:
            # Standard authentication error
            messages.error(request, 'Invalid username or password.')
            form = AuthenticationForm()
        else:
            # User authenticated successfully
            login(request, user)
            # Track login
            try:
                log_usage(request, 'login', f'User {user.username} logged in')
            except Exception as e:
                print(f"Error logging usage: {e}")
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
    else:
        form = AuthenticationForm()
    
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    """User logout view"""
    if request.user.is_authenticated:
        log_usage(request, 'logout', f'User {request.user.username} logged out')
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

def confirm_email(request, token):
    """Confirm user email via token link"""
    from .models import EmailConfirmation
    from .email_utils import send_welcome_email
    
    try:
        email_confirmation = EmailConfirmation.objects.get(token=token)
        
        # Check if already confirmed
        if email_confirmation.is_confirmed:
            messages.info(request, 'This email has already been confirmed. You can now log in.')
            return redirect('login')
        
        # Check if token has expired
        if email_confirmation.is_expired():
            messages.error(
                request,
                'This confirmation link has expired. Please register again or contact support.'
            )
            return redirect('register')
        
        # Confirm the email
        email_confirmation.confirm_email()
        
        # Send welcome email
        send_welcome_email(email_confirmation.user)
        
        messages.success(
            request,
            'Email confirmed successfully! You can now log in to your account.'
        )
        return redirect('login')
        
    except EmailConfirmation.DoesNotExist:
        messages.error(request, 'Invalid confirmation link. Please try again or contact support.')
        return redirect('register')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('home')

def resend_confirmation_email(request):
    """Resend confirmation email to user"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Please provide your email address.')
            return render(request, 'core/resend_confirmation.html')
        
        try:
            user = User.objects.get(email=email)
            
            # Check if user is already active
            if user.is_active:
                messages.info(request, 'Your account is already activated. You can log in now.')
                return redirect('login')
            
            # Check if confirmation email already exists
            from .models import EmailConfirmation
            email_conf = EmailConfirmation.objects.filter(user=user).first()
            
            if email_conf and not email_conf.is_expired():
                # Delete old confirmation and create new one
                email_conf.delete()
            
            # Send new confirmation email
            from .email_utils import send_confirmation_email
            sent = send_confirmation_email(user, request)
            
            if sent:
                messages.success(
                    request,
                    'Confirmation email has been resent. Please check your email to verify your account.'
                )
                return redirect('login')
            else:
                messages.error(request, 'Failed to send confirmation email. Please try again later.')
        
        except User.DoesNotExist:
            # Don't reveal if email exists or not (security best practice)
            messages.success(
                request,
                'If an account with that email exists and is not yet confirmed, a confirmation email has been sent.'
            )
            return redirect('login')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
    
    return render(request, 'core/resend_confirmation.html')

def health_assessment(request):
    """Health assessment and BMI calculation view"""
    if request.method == 'POST':
        try:
            # Get form data
            height = float(request.POST.get('height'))
            weight = float(request.POST.get('weight'))
            age = int(request.POST.get('age', 0))
            gender = request.POST.get('gender')
            activity_level = request.POST.get('activity')
            health_goal = request.POST.get('goal')
            dietary_preferences = request.POST.get('preferences', '')
            allergies = request.POST.get('allergies', '')
            
            # Validate data
            validation_errors = validate_health_data(height, weight, age)
            if validation_errors:
                for error in validation_errors:
                    messages.error(request, error)
                return render(request, 'core/health_assesment.html')
            
            # Calculate BMI
            bmi = calculate_bmi(height, weight)
            bmi_category = get_bmi_category(bmi)
            
            # Calculate calorie recommendations
            calorie_data = get_calorie_recommendation(
                bmi_category, weight, height, age, gender, activity_level
            )
            
            # Get health tips
            health_tips = get_health_tips(bmi_category)
            
            # Update user profile and save assessment only if user is authenticated
            meal_suggestions_data = generate_meal_suggestions(bmi_category, None)
            assessment = None
            if request.user.is_authenticated:
                profile, created = UserProfile.objects.get_or_create(user=request.user)
                if height: profile.height = height
                if weight: profile.weight = weight
                if gender: profile.gender = gender
                if activity_level: profile.activity_level = activity_level
                if dietary_preferences: profile.dietary_preferences = dietary_preferences
                if allergies: profile.food_allergies = allergies
                profile.save()

                # Calculate BMR and calorie recommendations
                from .utils import calculate_bmr
                bmr = calculate_bmr(weight, height, age, gender) if age else 0
                
                # Calculate maintenance and target calories using activity level
                activity_multipliers = {
                    'sedentary': 1.2,
                    'light': 1.375,
                    'moderate': 1.55,
                    'active': 1.725,
                    'very_active': 1.9
                }
                maintenance_calories = int(bmr * activity_multipliers.get(activity_level, 1.2))
                
                # Adjust target based on BMI category
                if bmi_category == "Underweight":
                    target_calories = maintenance_calories + 300
                elif bmi_category in ["Overweight", "Obese"]:
                    target_calories = maintenance_calories - 500
                else:
                    target_calories = maintenance_calories

                # Save assessment
                assessment = HealthAssessment.objects.create(
                    user=request.user,
                    height=height,
                    weight=weight,
                    age=age if age else None,
                    gender=gender,
                    activity_level=activity_level,
                    health_goal=health_goal,
                    bmi=bmi,
                    bmi_category=bmi_category,
                    bmr=bmr,
                    maintenance_calories=maintenance_calories,
                    target_calories=target_calories,
                    dietary_preferences=dietary_preferences,
                    food_allergies=allergies,
                    notes=f"Goal: {health_goal}, Activity: {activity_level}"
                )

                # Generate and save meal suggestions tied to assessment
                meal_suggestions_data = generate_meal_suggestions(bmi_category, profile)
                for meal_data in meal_suggestions_data:
                    MealSuggestion.objects.create(
                        health_assessment=assessment,
                        **meal_data
                    )
            
            context = {
                'assessment': assessment,
                'meal_suggestions': meal_suggestions_data,
                'bmi': bmi,
                'bmi_category': bmi_category,
                'calorie_data': calorie_data,
                'health_tips': health_tips,
                'health_goal': health_goal,
                'dietary_preferences': dietary_preferences,
                'allergies': allergies,
            }
            
            # Track usage
            if request.user.is_authenticated:
                log_usage(request, 'health_assessment', f'Completed assessment - BMI: {bmi:.1f}, Goal: {health_goal}')
                update_user_stats(request.user)
            
            return render(request, 'core/health_assesment.html', context)
            
        except (ValueError, TypeError) as e:
            messages.error(request, 'Please enter valid values for all fields.')
        except Exception as e:
            messages.error(request, 'An error occurred while processing your assessment.')
    
    # If user is authenticated, load profile and last assessment for pre-filling
    initial_data = {}
    profile = None
    last_assessment = None
    if request.user.is_authenticated:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        last_assessment = HealthAssessment.objects.filter(user=request.user).first()

        # Pre-fill form with profile data if available
        if profile.height:
            initial_data['height'] = profile.height
        if profile.weight:
            initial_data['weight'] = profile.weight
        if profile.gender:
            initial_data['gender'] = profile.gender
        if profile.activity_level:
            initial_data['activity_level'] = profile.activity_level
        if profile.dietary_preferences:
            initial_data['preferences'] = profile.dietary_preferences

    return render(request, 'core/health_assesment.html', {
        'last_assessment': last_assessment,
        'initial_data': initial_data,
        'profile': profile
    })

def health_assessment_api(request):
    """API endpoint for health assessment (AJAX)"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            height = float(data.get('height'))
            weight = float(data.get('weight'))
            age = int(data.get('age', 0))
            gender = data.get('gender')
            activity_level = data.get('activity')
            health_goal = data.get('goal')
            dietary_preferences = data.get('preferences', '')
            allergies = data.get('allergies', '')
            
            # Validate data
            validation_errors = validate_health_data(height, weight, age)
            if validation_errors:
                return JsonResponse({'error': validation_errors[0]}, status=400)
            
            # Calculate BMI
            bmi = calculate_bmi(height, weight)
            bmi_category = get_bmi_category(bmi)
            
            # Calculate calorie recommendations
            calorie_data = get_calorie_recommendation(
                bmi_category, weight, height, age, gender, activity_level
            )
            
            # Get health tips
            health_tips = get_health_tips(bmi_category)
            
            # Generate meal suggestions (use profile if user is authenticated)
            profile_obj = None
            if request.user.is_authenticated:
                profile_obj, created = UserProfile.objects.get_or_create(user=request.user)
            meal_suggestions = generate_meal_suggestions(bmi_category, profile_obj)
            
            # Save assessment if user is authenticated
            if request.user.is_authenticated:
                assessment = HealthAssessment.objects.create(
                    user=request.user,
                    height=height,
                    weight=weight,
                    bmi=bmi,
                    bmi_category=bmi_category,
                    notes=f"Goal: {health_goal}, Activity: {activity_level}, Allergies: {allergies}"
                )
                
                # Save meal suggestions
                for meal_data in meal_suggestions:
                    MealSuggestion.objects.create(
                        health_assessment=assessment,
                        **meal_data
                    )
            
            return JsonResponse({
                'success': True,
                'bmi': bmi,
                'bmi_category': bmi_category,
                'calorie_data': calorie_data,
                'health_tips': health_tips,
                'meal_suggestions': meal_suggestions,
                'dietary_preferences': dietary_preferences,
                'allergies': allergies,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'error': 'Please enter valid numeric values'}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'An error occurred during assessment'}, status=500)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def assessment_history(request):
    """View user's assessment history"""
    assessments = HealthAssessment.objects.filter(user=request.user).order_by('-assessment_date')
    
    # Calculate progress if multiple assessments exist
    progress_data = []
    if assessments.count() > 1:
        for i, assessment in enumerate(assessments):
            progress_data.append({
                'date': assessment.assessment_date.strftime('%Y-%m-%d'),
                'bmi': assessment.bmi,
                'weight': assessment.weight,
                'category': assessment.bmi_category
            })
    
    return render(request, 'core/assessment_history.html', {
        'assessments': assessments,
        'progress_data': progress_data
    })

@login_required
def assessment_detail(request, assessment_id):
    """View detailed information about a specific assessment"""
    try:
        assessment = HealthAssessment.objects.get(id=assessment_id, user=request.user)
        meals = assessment.meal_suggestions.all()
        
        # Calculate BMR if not already saved
        if not assessment.bmr:
            from .utils import calculate_bmr
            assessment.bmr = calculate_bmr(assessment.weight, assessment.height, 
                                          assessment.age or 30, assessment.gender)
            assessment.save()
        
        # Get health tips
        health_tips = get_health_tips(assessment.bmi_category)
        
        return render(request, 'core/assessment_detail.html', {
            'assessment': assessment,
            'meals': meals,
            'health_tips': health_tips
        })
    except HealthAssessment.DoesNotExist:
        messages.error(request, 'Assessment not found.')
        return redirect('assessment_history')

@login_required(login_url='login')
def chat_assistant(request):
    """AI chat assistant view"""
    return render(request, 'core/chat.html')

@login_required
def features(request):
    """Features page view - shows Favorite Meals, Articles, and Progress Tracking"""
    return render(request, 'core/features.html')

@csrf_exempt
@login_required
def chat_api(request):
    """API endpoint for AI chat assistant"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            conversation_id = data.get('conversation_id')
            language = data.get('language', 'en')
            model = data.get('model', 'nutrition')

            if not user_message:
                return JsonResponse({'error': 'Message cannot be empty'}, status=400)

            # Use a transaction to ensure messages and conversation updates are consistent
            with transaction.atomic():
                # Get or create conversation
                conversation = None
                if conversation_id:
                    try:
                        conversation = Conversation.objects.select_for_update().get(id=conversation_id, user=request.user)
                    except Conversation.DoesNotExist:
                        conversation = None

                if not conversation:
                    conversation = Conversation.objects.create(
                        user=request.user,
                        title=user_message[:50] + "..." if len(user_message) > 50 else user_message
                    )

                # Save user message
                user_msg_obj = Message.objects.create(
                    conversation=conversation,
                    message=user_message,
                    message_type='user'
                )

                # Generate AI response based on nutrition focus
                ai_response = generate_nutrition_response(user_message, model, request.user)

                # Save AI response
                ai_msg_obj = Message.objects.create(
                    conversation=conversation,
                    message=ai_response,
                    message_type='assistant'
                )

                # Update conversation metadata and timestamp
                if conversation.messages.count() <= 2:
                    # First meaningful exchange - set title
                    conversation.title = user_message[:50] + "..." if len(user_message) > 50 else user_message

                conversation.updated_at = timezone.now()
                conversation.save()

            return JsonResponse({
                'success': True,
                'response': ai_response,
                'conversation_id': conversation.id,
                'user_message_id': str(user_msg_obj.id),
                'ai_message_id': str(ai_msg_obj.id),
                'conversation_title': conversation.title,
                'conversation_updated_at': conversation.updated_at.isoformat()
            })

        except Exception as e:
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def generate_nutrition_response(user_message, model, user):
    """Generate nutrition-focused AI response"""
    user_message_lower = user_message.lower()
    
    # Nutrition-specific responses
    nutrition_responses = {
        'bmi': "BMI (Body Mass Index) is calculated using weight and height: BMI = weight(kg) / height(m)². A healthy range is 18.5-24.9. Would you like me to calculate yours?",
        'calorie': "Daily calorie needs vary by age, gender, weight, height, and activity level. Generally, women need 1,800-2,400 and men need 2,200-3,000 calories daily.",
        'protein': "Recommended protein intake is 0.8g per kg of body weight. Active individuals may need 1.2-2.0g per kg. For a 70kg person, that's 56-140g daily.",
        'breakfast': "Healthy breakfast ideas: Greek yogurt with berries, oatmeal with banana, scrambled eggs with spinach, smoothies, or avocado toast with eggs.",
        'meal': "For balanced meals, include protein (chicken, fish, tofu), complex carbs (whole grains, sweet potatoes), healthy fats (avocado, nuts), and vegetables.",
        'weight loss': "For weight loss, focus on calorie deficit, protein-rich foods, fiber, and regular exercise. Aim for 1-2 pounds per week for sustainable results.",
        'muscle gain': "For muscle building, increase protein intake (1.6-2.2g per kg), ensure calorie surplus, and combine with strength training.",
        'energy': "For sustained energy: complex carbs (oats, sweet potatoes), lean proteins, healthy fats, iron-rich foods, and proper hydration.",
        'hydration': "Aim for 8-10 glasses of water daily. Needs increase with exercise, heat, or high-protein diets.",
        'vegetarian': "Vegetarian protein sources: lentils, chickpeas, tofu, tempeh, quinoa, nuts, seeds, and dairy products.",
        'vegan': "Vegan protein sources: lentils, chickpeas, tofu, tempeh, seitan, edamame, quinoa, and various nuts and seeds.",
        'gluten': "Gluten-free options: rice, quinoa, corn, potatoes, gluten-free oats, and various fruits and vegetables.",
        'sugar': "Reduce added sugars by choosing whole fruits, reading labels, and using natural sweeteners like honey or maple syrup in moderation.",
    }
    
    # Check for nutrition keywords
    for keyword, response in nutrition_responses.items():
        if keyword in user_message_lower:
            return response
    
    # General nutrition responses
    if any(word in user_message_lower for word in ['hello', 'hi', 'hey']):
        return "Hello! I'm your FitWell assistant. I can help with nutrition advice, BMI calculations, meal planning, and health tips!"
    
    elif any(word in user_message_lower for word in ['thank', 'thanks']):
        return "You're welcome! Feel free to ask more nutrition questions anytime."
    
    elif any(word in user_message_lower for word in ['recipe', 'food']):
        return "I can suggest healthy recipes based on your dietary preferences. What type of cuisine or ingredients are you interested in?"
    
    elif any(word in user_message_lower for word in ['exercise', 'workout']):
        return "Exercise complements good nutrition! For weight loss, combine cardio with strength training. For muscle gain, focus on progressive overload in strength training."
    
    elif any(word in user_message_lower for word in ['supplement', 'vitamin']):
        return "While whole foods are best, common supplements include Vitamin D, Omega-3s, and protein powder. Consult a healthcare provider for personalized advice."
    
    # Default response for unknown queries
    return "I specialize in nutrition and health! Ask me about BMI, calories, meal planning, protein needs, or any other nutrition topic."

@login_required
def conversation_list_api(request):
    """API to get user's conversation list, sorted by most recent message first"""
    from django.db.models import Max
    from django.db.models.functions import Coalesce

    # Support pagination parameters
    try:
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))
    except ValueError:
        return JsonResponse({'error': 'Invalid pagination parameters'}, status=400)

    # DB-side ordering: pinned desc, then last message timestamp desc (fallback to updated_at)
    qs = (
        Conversation.objects.filter(user=request.user)
        .annotate(last_msg_ts=Max('messages__timestamp'))
        .annotate(sort_ts=Coalesce('last_msg_ts', 'updated_at'))
        .order_by('-pinned', '-sort_ts')
        .select_related('user')
    )

    total = qs.count()
    conversations = list(qs[offset:offset + limit])

    conversation_data = []
    for conv in conversations:
        # Get last message for preview and exact timestamp
        last_message = conv.messages.order_by('-timestamp').first()
        most_recent_timestamp = getattr(conv, 'sort_ts', None) or (last_message.timestamp if last_message else conv.updated_at)

        # compute unread count (messages after last_read_at)
        if conv.last_read_at:
            unread_count = conv.messages.filter(timestamp__gt=conv.last_read_at).count()
        else:
            unread_count = conv.messages.count()

        conversation_data.append({
            'id': str(conv.id),
            'title': conv.title,
            'pinned': conv.pinned,
            'unread_count': unread_count,
            'last_message': (last_message.message[:200] + '...') if last_message and len(last_message.message) > 200 else (last_message.message if last_message else ''),
            'last_message_type': last_message.message_type if last_message else None,
            'last_message_timestamp': last_message.timestamp.isoformat() if last_message else None,
            'updated_at': conv.updated_at.isoformat(),
            'created_at': conv.created_at.isoformat(),
            'display_timestamp': most_recent_timestamp.isoformat(),
            'message_count': conv.messages.count(),
            'sort_timestamp': most_recent_timestamp.timestamp(),
        })

    return JsonResponse({'conversations': conversation_data, 'total': total, 'limit': limit, 'offset': offset})


@login_required
@login_required
@csrf_protect
def rename_conversation_api(request, conversation_id):
    """API to rename a conversation"""
    if request.method in ('POST', 'PATCH'):
        try:
            data = json.loads(request.body or '{}')
            new_title = data.get('title', '').strip()
            if not new_title:
                return JsonResponse({'error': 'Title cannot be empty'}, status=400)

            conv = Conversation.objects.get(id=conversation_id, user=request.user)
            conv.title = new_title
            conv.save()
            return JsonResponse({'success': True, 'title': conv.title})
        except Conversation.DoesNotExist:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Error renaming conversation: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid method'}, status=400)


@login_required
@csrf_protect
def pin_conversation_api(request, conversation_id):
    """API to pin/unpin a conversation"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body or '{}')
            pinned = data.get('pinned')
            if pinned is None:
                return JsonResponse({'error': 'Pinned flag required'}, status=400)

            conv = Conversation.objects.get(id=conversation_id, user=request.user)
            conv.pinned = bool(pinned)
            conv.save()
            return JsonResponse({'success': True, 'pinned': conv.pinned})
        except Conversation.DoesNotExist:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Error updating pinned state: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid method'}, status=400)

@login_required
def conversation_detail_api(request, conversation_id):
    """API to get specific conversation details"""
    try:
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        messages = conversation.messages.order_by('timestamp')
        
        message_data = []
        for msg in messages:
            message_data.append({
                'id': msg.id,
                'message': msg.message,
                'type': msg.message_type,
                'timestamp': msg.timestamp.strftime('%H:%M')
            })
        # Mark conversation as read for this user
        try:
            conversation.last_read_at = timezone.now()
            conversation.save()
        except Exception:
            pass

        return JsonResponse({
            'success': True,
            'conversation': {
                'id': conversation.id,
                'title': conversation.title,
                'messages': message_data,
                'message_count': conversation.messages.count(),
                'updated_at': conversation.updated_at.isoformat()
            }
        })
        
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)

@login_required
@csrf_protect
def mark_conversation_read_api(request, conversation_id):
    """API to mark a conversation as read"""
    if request.method == 'POST':
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
            conversation.last_read_at = timezone.now()
            conversation.save()
            return JsonResponse({'success': True})
        except Conversation.DoesNotExist:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid method'}, status=400)

@login_required
@csrf_protect
def delete_conversation_api(request, conversation_id):
    """API to delete a conversation"""
    if request.method in ('DELETE', 'POST'):
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
            conversation.delete()
            return JsonResponse({'success': True})
        except Conversation.DoesNotExist:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid method'}, status=400)

@login_required
@csrf_protect
def clear_conversations_api(request):
    """API to clear all conversations"""
    if request.method == 'POST':
        conversations = Conversation.objects.filter(user=request.user)
        count = conversations.count()
        conversations.delete()
        return JsonResponse({'success': True, 'deleted_count': count})
    
    return JsonResponse({'error': 'Invalid method'}, status=400)

@csrf_exempt
@login_required
def text_to_speech_api(request):
    """API for text-to-speech functionality"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text = data.get('text', '')
            language = data.get('language', 'en')
            
            # In a real implementation, you would integrate with a TTS service
            # For now, we'll return a success response
            return JsonResponse({
                'success': True,
                'message': 'TTS functionality would be implemented here',
                'audio': None  # Base64 encoded audio would go here
            })
            
        except Exception as e:
            return JsonResponse({'error': f'TTS error: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
@login_required
def speech_to_text_api(request):
    """API for speech-to-text functionality"""
    if request.method == 'POST':
        try:
            # In a real implementation, you would process the audio file
            # For now, we'll return a mock response
            audio_file = request.FILES.get('audio')
            
            # Mock transcription
            mock_transcriptions = [
                "I want to know about healthy breakfast options",
                "How much protein should I eat daily?",
                "Can you calculate my BMI?",
                "What are good foods for energy?",
                "I need meal planning advice"
            ]
            
            import random
            transcribed_text = random.choice(mock_transcriptions)
            
            return JsonResponse({
                'success': True,
                'text': transcribed_text
            })
            
        except Exception as e:
            return JsonResponse({'error': f'STT error: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required(login_url='login')
def profile_view(request):
    """User profile view"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        try:
            profile.height = request.POST.get('height') or None
            profile.weight = request.POST.get('weight') or None
            profile.gender = request.POST.get('gender')
            profile.date_of_birth = request.POST.get('date_of_birth') or None
            profile.activity_level = request.POST.get('activity_level')
            profile.dietary_preferences = request.POST.get('dietary_preferences')
            profile.health_goals = request.POST.get('health_goals')
            # Handle both 'allergies' (from template) and 'food_allergies' (from model)
            allergies_input = request.POST.get('allergies') or request.POST.get('food_allergies')
            if allergies_input:
                profile.food_allergies = allergies_input
            profile.save()
            
            # Track profile update
            log_usage(request, 'profile_update', 'User updated their profile')
            update_user_stats(request.user)
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
            
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
    # Track profile view
    log_usage(request, 'view_profile', 'User viewed their profile')
    
    # Get user's assessment history
    assessments = HealthAssessment.objects.filter(user=request.user).order_by('-assessment_date')[:10]
    
    # Get conversation stats
    conversations = Conversation.objects.filter(user=request.user)
    total_conversations = conversations.count()
    total_messages = Message.objects.filter(conversation__user=request.user).count()
    
    # Calculate BMI stats
    total_assessments = assessments.count()
    latest_bmi = None
    latest_bmi_category = None
    bmi_trend = None
    weight_trend = None
    weight_change = None
    weight_change_percentage = None
    bmi_change_percentage = None
    
    if total_assessments > 0:
        latest_bmi = assessments[0].bmi
        latest_bmi_category = get_bmi_category(latest_bmi)
        bmi_trend = "stable"
        weight_trend = "stable"
        
        if total_assessments > 1:
            previous_bmi = assessments[1].bmi
            previous_weight = assessments[1].weight
            latest_weight = assessments[0].weight
            
            # Calculate weight change
            weight_change = round(latest_weight - previous_weight, 1)
            if previous_weight > 0:
                weight_change_percentage = round(((latest_weight - previous_weight) / previous_weight) * 100, 1)
            
            # Calculate BMI change percentage
            if previous_bmi > 0:
                bmi_change_percentage = round(((latest_bmi - previous_bmi) / previous_bmi) * 100, 1)
            
            if latest_bmi > previous_bmi:
                bmi_trend = "increasing"
            elif latest_bmi < previous_bmi:
                bmi_trend = "decreasing"
            
            if latest_weight > previous_weight:
                weight_trend = "increasing"
            elif latest_weight < previous_weight:
                weight_trend = "decreasing"
    
    return render(request, 'core/profile.html', {
        'profile': profile,
        'assessments': assessments,
        'total_assessments': total_assessments,
        'latest_bmi': latest_bmi,
        'latest_bmi_category': latest_bmi_category,
        'bmi_trend': bmi_trend,
        'weight_trend': weight_trend,
        'weight_change': weight_change,
        'weight_change_percentage': weight_change_percentage,
        'bmi_change_percentage': bmi_change_percentage,
        'total_conversations': total_conversations,
        'total_messages': total_messages
    })

@login_required
def profile_api(request):
    """API endpoint for user profile data"""
    if request.method == 'GET':
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        profile_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'height': profile.height,
            'weight': profile.weight,
            'gender': profile.gender,
            'date_of_birth': profile.date_of_birth.strftime('%Y-%m-%d') if profile.date_of_birth else None,
            'activity_level': profile.activity_level,
            'dietary_preferences': profile.dietary_preferences,
            'health_goals': profile.health_goals,
        }
        
        return JsonResponse({'success': True, 'user': profile_data})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def delete_account(request):
    """Handle user account deletion"""
    if request.method == 'POST':
        user = request.user
        # Logout before deletion to prevent issues
        logout(request)
        # Delete the user - this will cascade to profile via Django's default behavior
        user.delete()
        messages.success(request, 'Your account has been permanently deleted.')
        return redirect('home')
    
    # If GET request, show confirmation page
    return render(request, 'core/delete_account_confirm.html')

@csrf_exempt
@login_required
def set_language_api(request):
    """API to set user language preference"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            language = data.get('language', 'en')
            
            # Update user profile with language preference
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.language = language
            profile.save()
            
            return JsonResponse({'success': True, 'language': language})
            
        except Exception as e:
            return JsonResponse({'error': f'Error setting language: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
def ocr_api(request):
    """API endpoint to accept an uploaded image and return OCR'd text.

    Accepts multipart/form-data with a file field named 'image'. Uses
    `pytesseract` + `Pillow` when available. If dependencies or the
    tesseract binary are missing, returns a helpful error message.
    """
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please log in to use OCR feature'}, status=401)

    if request.method == 'POST':
        # Support multipart form uploads
        image_file = request.FILES.get('image')
        if not image_file:
            return JsonResponse({'error': 'No image file uploaded (use field `image`).'}, status=400)

        # Try to import OCR dependencies and verify Tesseract availability
        try:
            from PIL import Image, ImageOps, ImageFilter, ImageEnhance
            import pytesseract
        except Exception as e:
            return JsonResponse({
                'error': 'OCR dependencies missing. Install Python packages `pillow` and `pytesseract`, and ensure the Tesseract binary is installed.',
                'details': str(e)
            }, status=500)

        # Check if tesseract binary is available and responding
        try:
            # This will raise if binary not found or not working
            _ = pytesseract.get_tesseract_version()
        except Exception as te:
            return JsonResponse({
                'error': 'Tesseract binary not found or not working. Install Tesseract and ensure it is on your PATH (e.g., `brew install tesseract` on macOS).',
                'details': str(te)
            }, status=500)

        try:
            # Open image from uploaded InMemoryUploadedFile
            img = Image.open(image_file)

            # Normalize image mode
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Basic preprocessing to improve OCR accuracy:
            # - convert to grayscale
            # - optionally resize if image is small
            # - sharpen
            gray = ImageOps.grayscale(img)

            # Resize up to a maximum dimension to help OCR on small images
            try:
                width, height = gray.size
                max_dim = 1600
                if max(width, height) < max_dim:
                    scale = max_dim / max(width, height)
                    new_size = (int(width * scale), int(height * scale))
                    gray = gray.resize(new_size, Image.LANCZOS)
            except Exception:
                # If resizing fails, continue with original
                pass

            # Sharpen and enhance contrast
            try:
                gray = gray.filter(ImageFilter.SHARPEN)
                enhancer = ImageEnhance.Contrast(gray)
                gray = enhancer.enhance(1.2)
            except Exception:
                pass

            # Run OCR (default language: English). If you need other languages, specify with `lang` param.
            text = pytesseract.image_to_string(gray)

            return JsonResponse({'success': True, 'text': text})
        except Exception as e:
            return JsonResponse({'error': f'OCR processing failed: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


def test_ocr_button(request):
    """Test page for OCR button functionality"""
    return render(request, 'core/test_ocr.html')


# ============ Favorite Meals APIs ============
@login_required
def favorite_meals_list_api(request):
    """Get user's favorite meals"""
    try:
        favorites = FavoriteMeal.objects.filter(user=request.user).select_related('meal_suggestion').order_by('-added_date')
        meal_data = []
        for fav in favorites:
            meal_data.append({
                'id': fav.id,
                'meal_id': fav.meal_suggestion.id,
                'name': fav.meal_suggestion.name,
                'description': fav.meal_suggestion.description,
                'calories': fav.meal_suggestion.calories,
                'protein': fav.meal_suggestion.protein,
                'carbs': fav.meal_suggestion.carbs,
                'fats': fav.meal_suggestion.fats,
                'meal_type': fav.meal_suggestion.meal_type,
                'rating': fav.rating,
                'notes': fav.notes,
                'added_date': fav.added_date.isoformat(),
            })
        return JsonResponse({'favorites': meal_data, 'total': len(meal_data)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def favorite_meals_add_api(request):
    """Add a meal to favorites"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    
    try:
        data = json.loads(request.body or '{}')
        meal_id = data.get('meal_id')
        rating = data.get('rating')
        notes = data.get('notes', '')
        
        if not meal_id:
            return JsonResponse({'error': 'meal_id required'}, status=400)
        
        # Convert meal_id to integer
        try:
            meal_id = int(meal_id)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid meal_id format'}, status=400)
        
        # Convert rating to integer if provided
        if rating is not None:
            try:
                rating = int(rating)
                if rating < 1 or rating > 5:
                    return JsonResponse({'error': 'Rating must be between 1 and 5'}, status=400)
            except (ValueError, TypeError):
                rating = None
        
        meal = MealSuggestion.objects.get(id=meal_id)
        fav, created = FavoriteMeal.objects.get_or_create(
            user=request.user,
            meal_suggestion=meal,
            defaults={'rating': rating, 'notes': notes}
        )
        
        if not created:
            fav.rating = rating
            fav.notes = notes
            fav.save()
        
        return JsonResponse({'success': True, 'created': created, 'favorite_id': fav.id})
    except MealSuggestion.DoesNotExist:
        return JsonResponse({'error': f'Meal not found (ID: {meal_id})'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)


@login_required
def favorite_meals_delete_api(request, favorite_id):
    """Remove a meal from favorites"""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    
    try:
        fav = FavoriteMeal.objects.get(id=favorite_id, user=request.user)
        fav.delete()
        return JsonResponse({'success': True})
    except FavoriteMeal.DoesNotExist:
        return JsonResponse({'error': 'Favorite not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def available_meals_api(request):
    """Get available meals from user's health assessments or all meals if none exist"""
    try:
        # First try to get meals from user's own health assessments
        meals = MealSuggestion.objects.filter(
            health_assessment__user=request.user
        ).values('id', 'name', 'calories', 'protein', 'carbs', 'fats', 'meal_type').distinct().order_by('-id')
        
        # If user has no meals from assessments, return all available meals
        if not meals.exists():
            meals = MealSuggestion.objects.all().values(
                'id', 'name', 'calories', 'protein', 'carbs', 'fats', 'meal_type'
            ).order_by('name')[:50]
        
        meal_data = list(meals)
        
        return JsonResponse({
            'meals': meal_data,
            'total': len(meal_data)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============ Nutrition Articles APIs ============
@login_required
def nutrition_articles_list_api(request):
    """Get published nutrition articles"""
    try:
        from .models import NutritionArticle
        category = request.GET.get('category')
        
        articles_qs = NutritionArticle.objects.filter(is_published=True).order_by('-published_date')
        if category:
            articles_qs = articles_qs.filter(category=category)
        
        articles = articles_qs[:50]  # Limit to 50
        article_data = []
        for article in articles:
            article_data.append({
                'id': article.id,
                'title': article.title,
                'summary': article.summary or article.content[:200],
                'category': article.category,
                'author': article.author or 'FitWell',
                'published_date': article.published_date.isoformat(),
                'read_time': article.read_time,
                'image_url': article.image_url,
                'slug': article.slug,
            })
        
        categories = [cat[0] for cat in NutritionArticle.CATEGORY_CHOICES]
        return JsonResponse({
            'articles': article_data,
            'total': len(article_data),
            'categories': categories
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def nutrition_articles_detail_api(request, article_id):
    """Get full article content"""
    try:
        from .models import NutritionArticle
        article = NutritionArticle.objects.get(id=article_id, is_published=True)
        
        return JsonResponse({
            'id': article.id,
            'title': article.title,
            'content': article.content,
            'summary': article.summary,
            'category': article.category,
            'author': article.author or 'FitWell',
            'published_date': article.published_date.isoformat(),
            'read_time': article.read_time,
            'image_url': article.image_url,
            'slug': article.slug,
            'keywords': article.keywords,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============ Progress Tracking APIs ============
@login_required
def progress_tracking_list_api(request):
    """Get user's progress entries"""
    try:
        from .models import ProgressTracking
        entries = ProgressTracking.objects.filter(user=request.user).order_by('-date')[:100]
        
        entry_data = []
        for entry in entries:
            entry_data.append({
                'id': entry.id,
                'date': entry.date.isoformat(),
                'weight': entry.weight,
                'bmi': entry.bmi,
                'calories_consumed': entry.calories_consumed,
                'calories_burned': entry.calories_burned,
                'water_intake': entry.water_intake,
                'steps': entry.steps,
                'workout_minutes': entry.workout_minutes,
                'mood_level': entry.mood_level,
                'energy_level': entry.energy_level,
                'notes': entry.notes,
            })
        
        return JsonResponse({'entries': entry_data, 'total': len(entry_data)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def progress_tracking_add_api(request):
    """Add a progress entry"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    
    try:
        from .models import ProgressTracking
        from datetime import datetime
        data = json.loads(request.body or '{}')
        
        # Convert date string to date object if it's a string
        date_value = data.get('date')
        if isinstance(date_value, str):
            date_value = datetime.strptime(date_value, '%Y-%m-%d').date()
        
        entry, created = ProgressTracking.objects.update_or_create(
            user=request.user,
            date=date_value,
            defaults={
                'weight': data.get('weight'),
                'bmi': data.get('bmi'),
                'calories_consumed': data.get('calories_consumed'),
                'calories_burned': data.get('calories_burned'),
                'water_intake': data.get('water_intake'),
                'steps': data.get('steps'),
                'workout_minutes': data.get('workout_minutes'),
                'mood_level': data.get('mood_level'),
                'energy_level': data.get('energy_level'),
                'notes': data.get('notes', ''),
            }
        )
        
        return JsonResponse({
            'success': True,
            'created': created,
            'entry_id': entry.id,
            'date': entry.date.isoformat() if hasattr(entry.date, 'isoformat') else str(entry.date)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def progress_tracking_delete_api(request, entry_id):
    """Delete a progress entry"""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    
    try:
        from .models import ProgressTracking
        entry = ProgressTracking.objects.get(id=entry_id, user=request.user)
        entry.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ============ PDF Export APIs ============
from io import BytesIO
from django.http import HttpResponse

@login_required
def export_progress_tracking_pdf(request):
    """Export progress tracking entries as PDF"""
    from datetime import datetime, timedelta
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    
    try:
        period = request.GET.get('period', 'monthly')  # 'daily', 'weekly' or 'monthly'
        
        # Calculate date range
        today = timezone.now().date()
        if period == 'daily':
            start_date = today
        elif period == 'weekly':
            start_date = today - timedelta(days=today.weekday())
        else:  # monthly
            start_date = today.replace(day=1)
        
        # Get entries for the period
        from .models import ProgressTracking
        entries = ProgressTracking.objects.filter(
            user=request.user,
            date__gte=start_date,
            date__lte=today
        ).order_by('date')
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#10B981'),
            spaceAfter=6,
            alignment=1
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#059669'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Add title
        period_text = 'Weekly' if period == 'weekly' else 'Monthly'
        elements.append(Paragraph(f'FitWell Progress Tracking Report - {period_text}', title_style))
        elements.append(Paragraph(f'Report Period: {start_date} to {today}', styles['Normal']))
        elements.append(Spacer(1, 0.3 * 72))
        
        if not entries.exists():
            elements.append(Paragraph('No entries for this period.', styles['Normal']))
        else:
            # Add statistics
            avg_weight = sum(e.weight for e in entries if e.weight) / len([e for e in entries if e.weight]) if any(e.weight for e in entries) else 0
            elements.append(Paragraph('Summary Statistics', heading_style))
            summary_data = [
                ['Metric', 'Value'],
                ['Total Entries', str(entries.count())],
                ['Average Weight', f'{avg_weight:.1f} kg' if avg_weight else 'N/A'],
            ]
            summary_table = Table(summary_data, colWidths=[3 * 72, 3 * 72])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10B981')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 0.3 * 72))
            
            # Add entries table
            elements.append(Paragraph('Detailed Entries', heading_style))
            table_data = [['Date', 'Weight (kg)', 'Notes']]
            
            for entry in entries:
                table_data.append([
                    str(entry.date),
                    str(entry.weight) if entry.weight else '-',
                    (entry.notes[:50] + '...') if entry.notes and len(entry.notes) > 50 else (entry.notes or '-')
                ])
            
            table = Table(table_data, colWidths=[1.5 * 72, 1.5 * 72, 2.5 * 72])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10B981')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            elements.append(table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="progress_tracking_{period}_{today}.pdf"'
        return response
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def export_health_assessment_pdf(request):
    """Export health assessment as PDF"""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    
    try:
        assessment_id = request.GET.get('id')
        if not assessment_id:
            return JsonResponse({'error': 'Assessment ID required'}, status=400)
        
        assessment = HealthAssessment.objects.get(id=assessment_id, user=request.user)
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#10B981'),
            spaceAfter=6,
            alignment=1
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#059669'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Add title
        elements.append(Paragraph('FitWell Health Assessment Report', title_style))
        elements.append(Paragraph(f'Assessment Date: {assessment.assessment_date.strftime("%B %d, %Y")}', styles['Normal']))
        elements.append(Spacer(1, 0.3 * 72))
        
        # Personal Information
        elements.append(Paragraph('Personal Information', heading_style))
        personal_data = [
            ['Height', f'{assessment.height} cm'],
            ['Weight', f'{assessment.weight} kg'],
            ['Age', str(assessment.age) if assessment.age else 'N/A'],
            ['Gender', assessment.gender.title() if assessment.gender else 'N/A'],
            ['Activity Level', assessment.activity_level.replace('_', ' ').title() if assessment.activity_level else 'N/A'],
            ['Health Goal', assessment.health_goal.replace('_', ' ').title() if assessment.health_goal else 'N/A'],
        ]
        personal_table = Table(personal_data, colWidths=[3 * 72, 3 * 72])
        personal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#10B981')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(personal_table)
        elements.append(Spacer(1, 0.3 * 72))
        
        # Health Metrics
        elements.append(Paragraph('Health Metrics', heading_style))
        metrics_data = [
            ['Metric', 'Value', 'Status'],
            ['BMI', f'{assessment.bmi:.1f}', assessment.bmi_category],
            ['BMR', f'{assessment.bmr:.0f} cal/day' if assessment.bmr else 'N/A', 'Basal Metabolic Rate'],
            ['Maintenance Calories', f'{assessment.maintenance_calories} cal/day' if assessment.maintenance_calories else 'N/A', 'Daily'],
            ['Target Calories', f'{assessment.target_calories} cal/day' if assessment.target_calories else 'N/A', 'Daily Goal'],
        ]
        metrics_table = Table(metrics_data, colWidths=[2 * 72, 2 * 72, 2 * 72])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10B981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 0.3 * 72))
        
        # Dietary Information
        if assessment.dietary_preferences or assessment.food_allergies:
            elements.append(Paragraph('Dietary Information', heading_style))
            dietary_data = []
            if assessment.dietary_preferences:
                dietary_data.append(['Dietary Preferences', assessment.dietary_preferences])
            if assessment.food_allergies:
                dietary_data.append(['Food Allergies', assessment.food_allergies])
            
            dietary_table = Table(dietary_data, colWidths=[3 * 72, 3 * 72])
            dietary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#10B981')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('WRAP', (1, 0), (1, -1), True),
                ('BACKGROUND', (1, 0), (1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            elements.append(dietary_table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="health_assessment_{assessment.assessment_date.strftime("%Y_%m_%d")}.pdf"'
        return response
        
    except HealthAssessment.DoesNotExist:
        return JsonResponse({'error': 'Assessment not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
