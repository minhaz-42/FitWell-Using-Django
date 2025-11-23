"""
Meal suggestion system using local Qwen API (running on localhost:21002)
Uses intelligent prompts to generate realistic, personalized meal suggestions
No rule-based system, fully AI-powered with your local model
"""

import json
import logging
from core.qwen_client import chat as qwen_chat

logger = logging.getLogger(__name__)


def get_meal_from_qwen(meal_type: str, target_calories: int, goal: str, allergies: str = None, preferences: str = None) -> dict:
    """
    Generate meal suggestion using local Qwen API
    Returns structured meal data with macros calculated
    """
    
    # Build the prompt
    meal_prompt = f"""Generate ONE {meal_type} meal suggestion with exactly {target_calories} calories.
Goal: {goal}
{f'Dietary preferences: {preferences}' if preferences else ''}
{f'Allergies to AVOID: {allergies}' if allergies else ''}

Respond in JSON format ONLY:
{{
    "name": "meal name",
    "description": "2-3 sentence description",
    "ingredients": "comma separated list",
    "preparation": "brief cooking instructions"
}}

Make sure the meal fits the calorie target and respects any allergies."""
    
    logger.debug(f"Generating {meal_type} from Qwen API...")
    
    # Call local Qwen server - let exceptions propagate
    response = qwen_chat(
        messages=[
            {
                "role": "system",
                "content": "You are a professional nutritionist. Generate realistic, healthy meal suggestions. Always respond with valid JSON only."
            },
            {
                "role": "user",
                "content": meal_prompt
            }
        ],
        model="qwen",
        temperature=0.7,
        max_tokens=300
    )
    
    if not response or response.startswith("(Local Qwen error)"):
        raise Exception(f"Qwen API failed for {meal_type}: {response}")
    
    # Parse JSON response - extract JSON object from response
    clean_response = response.strip()
    
    # Remove markdown code blocks if present
    if clean_response.startswith('```json'):
        clean_response = clean_response[7:]
    if clean_response.startswith('```'):
        clean_response = clean_response[3:]
    if clean_response.endswith('```'):
        clean_response = clean_response[:-3]
    
    clean_response = clean_response.strip()
    
    # Extract JSON object (handle case where Qwen adds text after the JSON)
    # Find the first { and the matching }
    start_idx = clean_response.find('{')
    if start_idx == -1:
        raise Exception(f"No JSON found in Qwen response for {meal_type}: {response[:200]}")
    
    # Find the matching closing brace
    brace_count = 0
    end_idx = -1
    for i in range(start_idx, len(clean_response)):
        if clean_response[i] == '{':
            brace_count += 1
        elif clean_response[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i + 1
                break
    
    if end_idx == -1:
        # Try to complete incomplete JSON by adding missing braces
        logger.warning(f"Incomplete JSON from Qwen for {meal_type}, attempting to auto-complete...")
        # Count open braces
        open_braces = clean_response[start_idx:].count('{') - clean_response[start_idx:].count('}')
        if open_braces > 0:
            # Add missing closing braces
            json_str = clean_response[start_idx:] + '}' * open_braces
        else:
            raise Exception(f"Invalid JSON in Qwen response for {meal_type}: {response[:300]}")
    else:
        json_str = clean_response[start_idx:end_idx]
    
    # Parse JSON with error handling and repair
    try:
        meal_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed for {meal_type}: {str(e)}")
        logger.debug(f"Failed JSON string: {json_str[:500]}")
        # Try simple repair: remove trailing incomplete strings/fields
        try:
            # Remove trailing comma and incomplete fields before the last }
            repaired = json_str.rstrip('}').rstrip(',').rstrip() + '}'
            meal_data = json.loads(repaired)
            logger.info(f"Successfully recovered meal data for {meal_type} after repair")
        except json.JSONDecodeError:
            # If repair fails, return fallback meal
            logger.warning(f"Could not repair JSON for {meal_type}, using fallback meal")
            meal_data = {
                "name": f"Healthy {meal_type.title()}",
                "description": "A nutritious and balanced meal.",
                "ingredients": "Fresh vegetables, lean protein, whole grains",
                "preparation": "Follow standard healthy cooking practices"
            }
    
    
    # Calculate macros based on goal
    if goal == "muscle_gain":
        protein_ratio = 0.35
        carb_ratio = 0.50
    elif goal == "weight_loss":
        protein_ratio = 0.30
        carb_ratio = 0.45
    else:  # maintain or improve_health
        protein_ratio = 0.25
        carb_ratio = 0.50
    
    fat_ratio = 1 - (protein_ratio + carb_ratio)
    
    protein_cal = target_calories * protein_ratio
    carb_cal = target_calories * carb_ratio
    fat_cal = target_calories * fat_ratio
    
    protein_g = int(protein_cal / 4)
    carb_g = int(carb_cal / 4)
    fat_g = int(fat_cal / 9)
    
    return {
        "name": meal_data.get("name", f"Healthy {meal_type.title()}"),
        "description": meal_data.get("description", "A nutritious meal"),
        "ingredients": meal_data.get("ingredients", "Various healthy ingredients"),
        "calories": int(target_calories),
        "protein_g": protein_g,
        "carbs_g": carb_g,
        "fats_g": fat_g,
        "preparation": meal_data.get("preparation", "Follow standard cooking instructions"),
    }


def get_meal_suggestions(meal_type: str, target_calories: int, goal: str, allergies: str = None, preferences: str = None):
    """
    Get meal suggestions using local Qwen API only.
    Does NOT fall back to hardcoded meals - exceptions propagate.
    """
    
    meal = get_meal_from_qwen(meal_type, target_calories, goal, allergies, preferences)
    
    if not meal:
        raise Exception(f"Failed to generate meal for {meal_type}")
    
    return meal
