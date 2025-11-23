from ninja import NinjaAPI
from ninja.security import django_auth
from typing import Optional
from pydantic import BaseModel
import base64
import io
from PIL import Image
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
import logging
from core.qwen_client import chat as qwen_chat
import os
import uuid
import requests
from django.utils import timezone

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Create API instance
api = NinjaAPI(urls_namespace='api_v1')

NUTRITION_SYSTEM_PROMPT = """
You are an expert nutrition and health advisor. Provide evidence-based advice about:
- Nutrition and diet
- Exercise and physical activity
- Health and wellness
- Weight management
- Meal planning
Keep responses concise, practical, and tailored to the user's health context when provided.
"""

class ChatRequest(BaseModel):
    message: str
    model: str = "nutrition"
    language: str = "en"
    bmi_category: Optional[str] = None
    images: Optional[list] = None  # Optional list of base64 data URLs or raw base64 strings

class ChatResponse(BaseModel):
    response: str
    conversation_id: Optional[str] = None
    user_message_id: Optional[str] = None
    ai_message_id: Optional[str] = None
    conversation_title: Optional[str] = None
    conversation_updated_at: Optional[str] = None
from django.db import transaction
from django.utils import timezone

class HealthAssessmentRequest(BaseModel):
    height: float  # cm
    weight: float  # kg
    age: int
    gender: str  # M, F, O
    activity: str  # sedentary, light, moderate, active, very_active
    goal: str  # weight_loss, maintain, muscle_gain, improve_health
    preferences: Optional[str] = None
    allergies: Optional[str] = None

class HealthAssessmentResponse(BaseModel):
    bmi: float
    bmi_category: str
    bmr: int
    maintenance_calories: int
    target_calories: int
    breakfast: dict
    lunch: dict
    dinner: dict
    analysis: str

@api.post("/health-assessment", response=HealthAssessmentResponse)
def health_assessment(request, data: HealthAssessmentRequest):
    """Generate personalized health assessment with AI-powered meal suggestions"""
    from core.models import HealthAssessment, MealSuggestion, UserProfile, UserStats
    
    logger.debug(f"Received health assessment request: {data}")
    
    try:
        # Calculate BMI
        height_m = data.height / 100
        bmi = round((data.weight / (height_m * height_m)) * 10) / 10
        
        # Determine BMI category
        if bmi < 18.5:
            bmi_category = "Underweight"
        elif bmi < 25:
            bmi_category = "Normal Weight"
        elif bmi < 30:
            bmi_category = "Overweight"
        else:
            bmi_category = "Obese"
        
        logger.debug(f"Calculated BMI: {bmi}, Category: {bmi_category}")
        
        # Calculate BMR (Mifflin-St Jeor)
        if data.gender == "M":
            bmr = int(10 * data.weight + 6.25 * data.height - 5 * data.age + 5)
        else:
            bmr = int(10 * data.weight + 6.25 * data.height - 5 * data.age - 161)
        
        # Apply activity multiplier
        activity_multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9
        }
        maintenance_calories = int(bmr * activity_multipliers.get(data.activity, 1.55))
        
        # Calculate target calories based on goal
        if data.goal == "weight_loss":
            target_calories = maintenance_calories - 500
        elif data.goal == "muscle_gain":
            target_calories = maintenance_calories + 500
        else:  # maintain or improve_health
            target_calories = maintenance_calories
        
        logger.debug(f"BMR: {bmr}, Maintenance: {maintenance_calories}, Target: {target_calories}")
        
        # Determine protein ratio based on goal
        if data.goal == "muscle_gain":
            protein_ratio = 0.35
        elif data.goal == "weight_loss":
            protein_ratio = 0.30
        else:
            protein_ratio = 0.25
        
        # Generate intelligent meal suggestions
        breakfast_calories = target_calories // 3
        lunch_calories = target_calories // 3
        dinner_calories = target_calories - breakfast_calories - lunch_calories
        
        # Try to generate meals from Qwen, fallback to defaults if it fails
        try:
            breakfast = generate_meal_suggestion(
                "breakfast",
                breakfast_calories,
                bmi_category,
                data.goal,
                data.preferences,
                data.allergies,
                protein_ratio
            )
        except Exception as e:
            logger.error(f"Failed to generate breakfast: {e}")
            raise
        
        try:
            lunch = generate_meal_suggestion(
                "lunch",
                lunch_calories,
                bmi_category,
                data.goal,
                data.preferences,
                data.allergies,
                protein_ratio
            )
        except Exception as e:
            logger.error(f"Failed to generate lunch: {e}")
            raise
        
        try:
            dinner = generate_meal_suggestion(
                "dinner",
                dinner_calories,
                bmi_category,
                data.goal,
                data.preferences,
                data.allergies,
                protein_ratio
            )
        except Exception as e:
            logger.error(f"Failed to generate dinner: {e}")
            raise
        
        # Generate health analysis
        analysis = generate_health_analysis(
            bmi,
            bmi_category,
            target_calories,
            data.goal,
            data.preferences,
            data.allergies
        )
        logger.debug(f"Generated analysis: {analysis}")
        
        # Save to database if user is authenticated
        if request.user and request.user.is_authenticated:
            try:
                # Create or update health assessment
                assessment = HealthAssessment.objects.create(
                    user=request.user,
                    height=data.height,
                    weight=data.weight,
                    age=data.age,
                    gender=data.gender,
                    activity_level=data.activity,
                    health_goal=data.goal,
                    bmi=bmi,
                    bmi_category=bmi_category,
                    bmr=bmr,
                    maintenance_calories=maintenance_calories,
                    target_calories=target_calories,
                    dietary_preferences=data.preferences or '',
                    food_allergies=data.allergies or '',
                    notes=f"Goal: {data.goal}, Activity: {data.activity}"
                )
                logger.debug(f"Saved health assessment {assessment.id}")
                
                # Save meal suggestions
                for meal_type, meal_data in [('breakfast', breakfast), ('lunch', lunch), ('dinner', dinner)]:
                    MealSuggestion.objects.create(
                        health_assessment=assessment,
                        meal_type=meal_type,
                        name=meal_data.get('name', ''),
                        description=meal_data.get('description', ''),
                        calories=meal_data.get('calories', 0),
                        protein=meal_data.get('protein_g', 0),
                        carbs=meal_data.get('carbs_g', 0),
                        fats=meal_data.get('fats_g', 0),
                        ingredients=str(meal_data.get('ingredients', ''))
                    )
                logger.debug(f"Saved meal suggestions for assessment {assessment.id}")
                
                # Update user profile
                profile, created = UserProfile.objects.get_or_create(user=request.user)
                profile.height = data.height
                profile.weight = data.weight
                profile.gender = data.gender
                profile.activity_level = data.activity
                profile.dietary_preferences = data.preferences or ''
                profile.food_allergies = data.allergies or ''
                profile.save()
                logger.debug(f"Updated user profile")
                
                # Update user stats
                stats, created = UserStats.objects.get_or_create(user=request.user)
                stats.total_assessments = HealthAssessment.objects.filter(user=request.user).count()
                stats.last_assessment_date = timezone.now()
                stats.save()
                logger.debug(f"Updated user stats")
                
            except Exception as e:
                logger.error(f"Failed to save assessment to database: {e}")
                # Continue anyway, return the calculated values
        
        return HealthAssessmentResponse(
            bmi=bmi,
            bmi_category=bmi_category,
            bmr=bmr,
            maintenance_calories=maintenance_calories,
            target_calories=target_calories,
            breakfast=breakfast,
            lunch=lunch,
            dinner=dinner,
            analysis=analysis
        )
        
    except Exception as e:
        logger.error(f"Error in health assessment: {str(e)}", exc_info=True)
        raise


def generate_health_analysis(bmi: float, bmi_category: str, target_calories: int, goal: str, preferences: str = None, allergies: str = None) -> str:
    """Generate personalized health analysis using Qwen API only"""
    
    analysis_prompt = f"""Provide a brief 2-3 sentence health recommendation for someone with:
BMI: {bmi:.1f} ({bmi_category})
Goal: {goal}
Target daily calories: {target_calories}
{f'Preferences: {preferences}' if preferences else ''}
{f'Allergies: {allergies}' if allergies else ''}

Be specific, personalized, and practical."""
    
    analysis = qwen_chat(
        messages=[
            {"role": "system", "content": "You are a professional health and nutrition advisor."},
            {"role": "user", "content": analysis_prompt}
        ],
        model="qwen",
        temperature=0.7,
        max_tokens=200
    )
    
    if not analysis or analysis.startswith("(Local Qwen error)"):
        raise Exception(f"Qwen API failed: {analysis}")
    
    return analysis.strip()


def generate_meal_suggestion(meal_type: str, calories: int, bmi_category: str, goal: str, preferences: str = None, allergies: str = None, protein_ratio: float = 0.25) -> dict:
    """Generate meal suggestions using local Qwen API only"""
    from core.meal_suggestions import get_meal_suggestions
    
    meal = get_meal_suggestions(meal_type, calories, goal, allergies, preferences)
    
    if not meal:
        raise Exception(f"Failed to generate meal for {meal_type}. Ensure Qwen server is running on port 21002.")
    
    return meal


class MealPlanPDFRequest(BaseModel):
    bmi: float
    bmi_category: str
    bmr: int
    maintenance_calories: int
    target_calories: int
    breakfast: dict
    lunch: dict
    dinner: dict
    analysis: str


@api.post("/health-assessment/download-pdf")
def download_meal_plan_pdf(request, data: MealPlanPDFRequest):
    """Generate and download meal plan as PDF"""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib import colors
    from datetime import datetime
    from django.http import HttpResponse
    
    # Create PDF in memory
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#4F46E5'),
        spaceAfter=12,
        alignment=1  # Center
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#4F46E5'),
        spaceAfter=10,
        spaceBefore=10
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    # Content
    story = []
    
    # Title
    story.append(Paragraph("🧠 NutriAI - Health Assessment Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", normal_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Health Metrics Section
    story.append(Paragraph("Health Metrics", heading_style))
    metrics_data = [
        ['Metric', 'Value'],
        ['BMI', f"{data.bmi} ({data.bmi_category})"],
        ['Basal Metabolic Rate (BMR)', f"{data.bmr:,} cal/day"],
        ['Maintenance Calories', f"{data.maintenance_calories:,} cal/day"],
        ['Target Daily Calories', f"{data.target_calories:,} cal/day"]
    ]
    
    metrics_table = Table(metrics_data, colWidths=[2.5*inch, 2.5*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Meal Plans Section
    story.append(Paragraph("Recommended Meal Plan", heading_style))
    
    # Helper function to get safe text from ingredients
    def get_ingredients_text(ingredients):
        if isinstance(ingredients, list):
            return ', '.join(ingredients)
        return str(ingredients) if ingredients else 'N/A'
    
    for meal_type in ['breakfast', 'lunch', 'dinner']:
        meal = data.__dict__[meal_type]
        
        story.append(Paragraph(f"<b>{meal_type.title()}</b>", ParagraphStyle(
            'MealType',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#4F46E5'),
            spaceAfter=6,
            spaceBefore=6
        )))
        
        # Meal details
        meal_details = f"""
        <b>Meal:</b> {meal.get('name', 'N/A')}<br/>
        <b>Description:</b> {meal.get('description', 'N/A')}<br/>
        <b>Calories:</b> {meal.get('calories', 0)} cal | 
        <b>Protein:</b> {meal.get('protein_g', 0)}g | 
        <b>Carbs:</b> {meal.get('carbs_g', 0)}g | 
        <b>Fats:</b> {meal.get('fats_g', 0)}g<br/>
        <b>Ingredients:</b> {get_ingredients_text(meal.get('ingredients', 'N/A'))}<br/>
        <b>Preparation:</b> {meal.get('preparation', 'N/A')}
        """
        story.append(Paragraph(meal_details, normal_style))
        story.append(Spacer(1, 0.2*inch))
    
    # Health Analysis Section
    story.append(Paragraph("Health Analysis & Recommendations", heading_style))
    story.append(Paragraph(data.analysis or "Assessment complete!", normal_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer_text = """
    <i>This report is based on your health assessment. For medical advice, please consult with a healthcare professional.<br/>
    NutriAI - Your Personal Nutrition AI Assistant</i>
    """
    story.append(Paragraph(footer_text, ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=1
    )))
    
    # Build PDF
    doc.build(story)
    
    # Return PDF as response
    pdf_buffer.seek(0)
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="NutriAI_MealPlan_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    return response


@api.post("/chat", response=ChatResponse)
def chat(request, data: ChatRequest):
    """Process chat messages, save to database, and return AI responses"""
    from core.models import Conversation, Message, UserStats
    
    logger.debug(f"Received chat request: {data}")
    
    try:
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            logger.warning("Chat request from unauthenticated user")
            raise Exception("User must be authenticated to use chat")
        
        # Get or create conversation
        conversation = None
        # Use transaction to keep conversation and messages consistent
        with transaction.atomic():
            # Get or create conversation
            conversation = None
            if data.__dict__.get('conversation_id'):
                try:
                    conversation = Conversation.objects.select_for_update().get(
                        id=data.__dict__.get('conversation_id'), 
                        user=request.user
                    )
                except Conversation.DoesNotExist:
                    logger.warning(f"Conversation {data.__dict__.get('conversation_id')} not found for user {request.user}")
                    conversation = None

            # Create new conversation if needed
            if not conversation:
                conversation = Conversation.objects.create(
                    user=request.user,
                    title=data.message[:50] + "..." if len(data.message) > 50 else data.message,
                    language=data.language,
                    model_used=data.model
                )
                logger.debug(f"Created new conversation {conversation.id}")

            # Save user message
            # Create message using conversation_id string to avoid SQLite UUID binding issues
            user_msg_obj = Message.objects.create(
                conversation_id=str(conversation.id),
                message=data.message,
                message_type='user'
            )
        logger.debug(f"Saved user message {user_msg_obj.id}")
        
        # Prepare the conversation context
        context = f"User BMI Category: {data.bmi_category}" if data.bmi_category else ""
        logger.debug(f"Context prepared: {context}")
        
        # Create messages for the assistant
        messages = [
            {"role": "system", "content": NUTRITION_SYSTEM_PROMPT}
        ]
        if context:
            messages.append({"role": "system", "content": context})
        # If images were attached, try to OCR them and include extracted text for context
        if data.images:
            ocr_texts = []
            for idx, img_item in enumerate(data.images, start=1):
                # img_item can be a data URL/base64 or a server URL path (starting with /static)
                img = None
                try:
                    if isinstance(img_item, str) and img_item.startswith('/static'):
                        # load from local static files
                        local_path = os.path.join(os.getcwd(), img_item.lstrip('/'))
                        logger.debug(f"Image {idx}: Loading from local path: {local_path}")
                        if not os.path.exists(local_path):
                            logger.error(f"Image {idx}: File not found at {local_path}")
                            ocr_texts.append(f"Image {idx}: (file not found at {local_path})")
                            continue
                        with open(local_path, 'rb') as f:
                            img = Image.open(io.BytesIO(f.read()))
                    elif isinstance(img_item, str) and img_item.startswith('http'):
                        # fetch remote image
                        logger.debug(f"Image {idx}: Fetching from HTTP URL: {img_item}")
                        try:
                            r = requests.get(img_item, timeout=5)
                            r.raise_for_status()
                            img = Image.open(io.BytesIO(r.content))
                        except requests.RequestException as req_err:
                            logger.error(f"Image {idx}: Failed to fetch from {img_item}: {req_err}")
                            ocr_texts.append(f"Image {idx}: (failed to fetch from URL)")
                            continue
                    else:
                        # assume base64 / data URL
                        logger.debug(f"Image {idx}: Processing as base64 data")
                        if isinstance(img_item, str) and img_item.startswith('data:'):
                            header, b64data = img_item.split(',', 1)
                        else:
                            b64data = img_item
                        try:
                            image_bytes = base64.b64decode(b64data)
                            img = Image.open(io.BytesIO(image_bytes))
                        except Exception as b64_err:
                            logger.error(f"Image {idx}: Failed to decode base64: {b64_err}")
                            ocr_texts.append(f"Image {idx}: (failed to decode image data)")
                            continue

                    if img is None:
                        logger.warning(f"Image {idx}: Image is None after loading")
                        ocr_texts.append(f"Image {idx}: (could not load image)")
                        continue

                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    logger.debug(f"Image {idx}: Running OCR on image (mode: {img.mode}, size: {img.size})")
                    if PYTESSERACT_AVAILABLE:
                        text = pytesseract.image_to_string(img)
                        text = text.strip()
                    else:
                        text = "(OCR not available - pytesseract not installed)"
                    logger.debug(f"Image {idx}: OCR result length: {len(text)} chars")
                    ocr_texts.append(f"Image {idx}: {text if text else '(no text found in image)'}")
                except Exception as e:
                    logger.error(f"Image {idx}: Unexpected error during OCR: {str(e)}", exc_info=True)
                    ocr_texts.append(f"Image {idx}: (error: {str(e)})")

            if ocr_texts:
                ocr_summary = "\n\n".join(ocr_texts)
                logger.info(f"Adding OCR summary to context: {ocr_summary[:200]}...")
                messages.append({"role": "system", "content": f"OCR extracted from attached images:\n\n{ocr_summary}"})
            else:
                logger.warning("No images could be processed for OCR")

        messages.append({"role": "user", "content": data.message})
        
        logger.debug(f"Sending request to Qwen with messages: {messages}")
        ai_response = qwen_chat(messages=messages, model="qwen", temperature=0.7, max_tokens=150)
        logger.debug(f"Received response from Qwen: {ai_response}")
        
        # Save AI response
        # Save AI response
        ai_msg_obj = Message.objects.create(
            conversation_id=str(conversation.id),
            message=ai_response,
            message_type='assistant'
        )

        # Update conversation metadata
        try:
            if conversation.messages.count() <= 2:
                conversation.title = data.message[:50] + "..." if len(data.message) > 50 else data.message
            conversation.updated_at = timezone.now()
            conversation.save()
        except Exception:
            pass
        logger.debug(f"Saved AI message {ai_msg_obj.id}")
        
        # Update user stats
        try:
            user_stats, created = UserStats.objects.get_or_create(user=request.user)
            user_stats.total_chat_messages = Message.objects.filter(conversation__user=request.user).count()
            user_stats.last_chat_date = timezone.now()
            user_stats.save()
            logger.debug(f"Updated user stats")
        except Exception as e:
            logger.error(f"Failed to update user stats: {e}")
        
        return ChatResponse(
            response=ai_response,
            conversation_id=str(conversation.id),
            user_message_id=str(user_msg_obj.id),
            ai_message_id=str(ai_msg_obj.id),
            conversation_title=conversation.title,
            conversation_updated_at=conversation.updated_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise


@api.post("/upload-image")
def upload_image(request):
    """Accept multipart file upload(s) and store under `static/uploads/`.
    Returns list of URL paths that can be used by the frontend and the chat endpoint.
    """
    try:
        # Ninja passes a wrapper request; its underlying Django request is in _request.
        django_req = getattr(request, '_request', request)
        files = []
        # support multiple file inputs named 'files' or single 'file'
        if hasattr(django_req.FILES, 'getlist') and django_req.FILES.getlist('files'):
            files = django_req.FILES.getlist('files')
        else:
            # fallback: take all uploaded files
            files = list(django_req.FILES.values())

        upload_dir = os.path.join(os.getcwd(), 'static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        saved_urls = []
        for f in files:
            ext = os.path.splitext(f.name)[1] or '.bin'
            fname = f"{uuid.uuid4().hex}{ext}"
            path = os.path.join(upload_dir, fname)
            with open(path, 'wb') as out:
                for chunk in f.chunks():
                    out.write(chunk)
            saved_urls.append(f"/static/uploads/{fname}")

        return {"urls": saved_urls}
    except Exception as e:
        logger.exception('Image upload failed')
        return {"urls": [], "error": str(e)}


@api.post("/test-ocr")
def test_ocr(request, data: ChatRequest):
    """Diagnostic endpoint to test OCR on images without calling the AI model"""
    ocr_results = []
    
    if not data.images:
        return {"error": "No images provided", "results": []}
    
    for idx, img_item in enumerate(data.images, start=1):
        result = {"image_index": idx, "source": "unknown", "success": False, "text": "", "error": None}
        
        try:
            img = None
            
            if isinstance(img_item, str) and img_item.startswith('/static'):
                result["source"] = "local_file"
                local_path = os.path.join(os.getcwd(), img_item.lstrip('/'))
                logger.debug(f"Test OCR {idx}: Loading from {local_path}")
                
                if not os.path.exists(local_path):
                    result["error"] = f"File not found: {local_path}"
                    ocr_results.append(result)
                    continue
                
                with open(local_path, 'rb') as f:
                    img = Image.open(io.BytesIO(f.read()))
                    
            elif isinstance(img_item, str) and img_item.startswith('http'):
                result["source"] = "http_url"
                try:
                    r = requests.get(img_item, timeout=5)
                    r.raise_for_status()
                    img = Image.open(io.BytesIO(r.content))
                except Exception as e:
                    result["error"] = f"Failed to fetch: {str(e)}"
                    ocr_results.append(result)
                    continue
                    
            else:
                result["source"] = "base64_data"
                try:
                    if isinstance(img_item, str) and img_item.startswith('data:'):
                        header, b64data = img_item.split(',', 1)
                    else:
                        b64data = img_item
                    image_bytes = base64.b64decode(b64data)
                    img = Image.open(io.BytesIO(image_bytes))
                except Exception as e:
                    result["error"] = f"Failed to decode base64: {str(e)}"
                    ocr_results.append(result)
                    continue
            
            if img is None:
                result["error"] = "Image object is None"
                ocr_results.append(result)
                continue
            
            result["image_mode"] = img.mode
            result["image_size"] = f"{img.width}x{img.height}"
            
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Run OCR
            if PYTESSERACT_AVAILABLE:
                text = pytesseract.image_to_string(img)
                text = text.strip()
            else:
                text = "(OCR not available - pytesseract not installed)"
            
            result["success"] = True
            result["text"] = text if text else "(no text found)"
            result["text_length"] = len(text)
            
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
            logger.error(f"Test OCR {idx}: {result['error']}", exc_info=True)
        
        ocr_results.append(result)
    
    return {
        "status": "OCR test completed",
        "total_images": len(data.images),
        "successful": sum(1 for r in ocr_results if r["success"]),
        "results": ocr_results
    }