from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
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

def home(request):
    """Home page view"""
    return render(request, 'core/home.html')

def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in - profile will be created by signal
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
    else:
        form = UserCreationForm()
    
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    """User login view"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Track login
            try:
                log_usage(request, 'login', f'User {user.username} logged in')
            except Exception as e:
                print(f"Error logging usage: {e}")
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
        else:
            # Form has errors, display them
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
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
        return "Hello! I'm your NutriAI assistant. I can help with nutrition advice, BMI calculations, meal planning, and health tips!"
    
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
    """API to get user's conversation list"""
    # Support pagination parameters
    try:
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))
    except ValueError:
        return JsonResponse({'error': 'Invalid pagination parameters'}, status=400)

    # Order by pinned first then most recently updated
    conversations_qs = Conversation.objects.filter(user=request.user).order_by('-pinned', '-updated_at')
    total = conversations_qs.count()
    conversations = conversations_qs[offset:offset+limit]

    conversation_data = []
    for conv in conversations:
        last_message = conv.messages.order_by('-timestamp').first()
        # compute unread count (messages after last_read_at)
        if conv.last_read_at:
            unread_count = conv.messages.filter(timestamp__gt=conv.last_read_at).count()
        else:
            unread_count = conv.messages.count()

        conversation_data.append({
            'id': conv.id,
            'title': conv.title,
            'pinned': conv.pinned,
            'unread_count': unread_count,
            'last_message': (last_message.message[:200] + '...') if last_message and len(last_message.message) > 200 else (last_message.message if last_message else ''),
            'last_message_type': last_message.message_type if last_message else None,
            'last_message_timestamp': last_message.timestamp.isoformat() if last_message else None,
            'updated_at': conv.updated_at.isoformat(),
            'message_count': conv.messages.count()
        })

    return JsonResponse({'conversations': conversation_data, 'total': total, 'limit': limit, 'offset': offset})


@login_required
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
def delete_conversation_api(request, conversation_id):
    """API to delete a conversation"""
    if request.method == 'DELETE':
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
            conversation.delete()
            return JsonResponse({'success': True})
        except Conversation.DoesNotExist:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid method'}, status=400)

@login_required
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
    bmi_trend = None
    weight_trend = None
    
    if total_assessments > 0:
        latest_bmi = assessments[0].bmi
        bmi_trend = "stable"
        weight_trend = "stable"
        
        if total_assessments > 1:
            previous_bmi = assessments[1].bmi
            previous_weight = assessments[1].weight
            
            if latest_bmi > previous_bmi:
                bmi_trend = "increasing"
            elif latest_bmi < previous_bmi:
                bmi_trend = "decreasing"
            
            if assessments[0].weight > previous_weight:
                weight_trend = "increasing"
            elif assessments[0].weight < previous_weight:
                weight_trend = "decreasing"
    
    return render(request, 'core/profile.html', {
        'profile': profile,
        'assessments': assessments,
        'total_assessments': total_assessments,
        'latest_bmi': latest_bmi,
        'bmi_trend': bmi_trend,
        'weight_trend': weight_trend,
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

        try:
            from PIL import Image
            import pytesseract
        except Exception as e:
            return JsonResponse({
                'error': 'OCR dependencies missing. Install Python packages `pillow` and `pytesseract`, and ensure the Tesseract binary is installed on your system.'
            }, status=500)

        try:
            # Open image from uploaded InMemoryUploadedFile
            img = Image.open(image_file)
            # Optionally convert to RGB for consistency
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Run OCR
            text = pytesseract.image_to_string(img)

            return JsonResponse({'success': True, 'text': text})
        except Exception as e:
            return JsonResponse({'error': f'OCR processing failed: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


def test_ocr_button(request):
    """Test page for OCR button functionality"""
    return render(request, 'core/test_ocr.html')