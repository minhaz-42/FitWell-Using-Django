from ninja import Router, Schema
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import requests
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from core.models import Conversation, Message
from core.utils import (
    calculate_bmi, get_bmi_category, get_health_tips,
    get_ideal_weight_range
)

# Import the v1 API
from .v1 import chat as chat_v1, ChatRequest
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = Router()

class MessageSchema(Schema):
    message: str
    model: str = "nutrition"
    language: str = "en"

class BMICalculateSchema(Schema):
    weight: float
    height: float

class BMIResponseSchema(Schema):
    bmi: float
    category: str
    message: str
    recommendations: List[str]

class MessageResponseSchema(Schema):
    success: bool
    response: str
    conversation_id: str
    user_message_id: int
    ai_message_id: int
    bmi_data: Optional[BMIResponseSchema] = None

class ConversationSchema(Schema):
    id: str
    title: str
    last_message: str
    timestamp: str
    message_count: int

class ConversationDetailSchema(Schema):
    id: str
    title: str
    messages: List[dict]

@router.post("/chat")
def chat_endpoint(request, payload: MessageSchema) -> MessageResponseSchema:
    """Process chat messages and return AI responses"""
    logger.debug(f"Received chat request with payload: {payload}")
    try:
        # Get current BMI category if available
        bmi_category = None
        if hasattr(request.session, 'bmi_category'):
            bmi_category = request.session.get('bmi_category')
        
        logger.debug(f"BMI category from session: {bmi_category}")
        
        # Use the v1 API directly
        chat_request = ChatRequest(
            message=payload.message,
            model=payload.model,
            language=payload.language,
            bmi_category=bmi_category
        )
        
        response = chat_v1(request, chat_request)
        ai_response = response.response
        
        # Store conversation if user is authenticated
        if request.user.is_authenticated:
            conversation = Conversation.objects.create(
                user=request.user,
                title=payload.message[:50] + "..." if len(payload.message) > 50 else payload.message
            )

            # Save user message
            user_msg = Message.objects.create(
                conversation=conversation,
                message=payload.message,
                message_type='user'
            )
            
            # Save AI response
            ai_msg = Message.objects.create(
                conversation=conversation,
                message=ai_response,
                message_type='assistant'
            )

            return MessageResponseSchema(
                success=True,
                response=ai_response,
                conversation_id=str(conversation.id),
                user_message_id=user_msg.id,
                ai_message_id=ai_msg.id
            )
        
        # For non-authenticated users, return response without saving
        return MessageResponseSchema(
            success=True,
            response=ai_response,
            conversation_id=str(uuid.uuid4()),
            user_message_id=1,
            ai_message_id=2
        )
        
    except requests.RequestException as e:
        # Handle API call errors
        error_message = f"Error communicating with AI service: {str(e)}"
        return MessageResponseSchema(
            success=False,
            response=error_message,
            conversation_id=str(uuid.uuid4()),
            user_message_id=1,
            ai_message_id=2
        )

@router.post("/calculate-bmi")
def calculate_bmi_endpoint(request, data: BMICalculateSchema) -> MessageResponseSchema:
    """Calculate BMI and provide personalized recommendations"""
    bmi = calculate_bmi(data.height, data.weight)
    category = get_bmi_category(bmi)
    
    # Store BMI category in session
    request.session['bmi_category'] = category
    
    # Get health tips based on BMI category
    tips = get_health_tips(category)
    
    # Calculate ideal weight range
    weight_range = get_ideal_weight_range(data.height, 'N/A')
    
    return MessageResponseSchema(
        success=True,
        response=f"Your BMI is {bmi}. This falls into the {category} category.",
        conversation_id=str(uuid.uuid4()),
        user_message_id=1,
        ai_message_id=2,
        bmi_data=BMIResponseSchema(
            bmi=bmi,
            category=category,
            message=(
                f"For your height of {data.height}cm, "
                f"a healthy weight range would be between {weight_range['min']}kg and {weight_range['max']}kg."
            ),
            recommendations=tips
        )
    )

@router.get("/conversations", response=List[ConversationSchema])
def list_conversations(request):
    """Get list of user's conversations"""
    if not request.user.is_authenticated:
        return []

    conversations = Conversation.objects.filter(user=request.user).order_by('-updated_at')
    result = []
    for conv in conversations:
        last_message = conv.messages.order_by('-timestamp').first()
        result.append({
            "id": str(conv.id),
            "title": conv.title,
            "last_message": last_message.message if last_message else "",
            "timestamp": conv.updated_at.strftime('%H:%M'),
            "message_count": conv.messages.count()
        })
    return result

@router.get("/conversations/{conversation_id}", response=ConversationDetailSchema)
def get_conversation(request, conversation_id: str):
    """Get details of a specific conversation"""
    if not request.user.is_authenticated:
        return {"error": "Authentication required"}

    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    messages = conversation.messages.order_by('timestamp')

    message_data = [{
        "id": msg.id,
        "message": msg.message,
        "type": msg.message_type,
        "timestamp": msg.timestamp.strftime('%H:%M')
    } for msg in messages]

    return {
        "id": str(conversation.id),
        "title": conversation.title,
        "messages": message_data
    }

@router.delete("/conversations/{conversation_id}")
def delete_conversation(request, conversation_id: str):
    """Delete a conversation"""
    if not request.user.is_authenticated:
        return {"success": False, "error": "Authentication required"}

    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    conversation.delete()
    return {"success": True}

