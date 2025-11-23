# core/utils.py

def calculate_bmi(height_cm, weight_kg):
    """Calculate BMI given height in cm and weight in kg"""
    try:
        height_m = height_cm / 100
        bmi = weight_kg / (height_m ** 2)
        return round(bmi, 1)
    except (TypeError, ZeroDivisionError):
        return None

def get_bmi_category(bmi):
    """Get BMI category based on BMI value"""
    if bmi is None:
        return "Invalid data"
    
    if bmi < 18.5:
        return "Underweight"
    elif 18.5 <= bmi < 25:
        return "Normal weight"
    elif 25 <= bmi < 30:
        return "Overweight"
    else:
        return "Obese"

def get_calorie_recommendation(bmi_category, weight, height, age, gender, activity_level):
    """Calculate daily calorie recommendations based on user profile"""
    # Basal Metabolic Rate (BMR) calculation using Mifflin-St Jeor Equation
    if gender == 'M':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:  # Female or Other
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    
    # Activity multiplier
    activity_multipliers = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'very_active': 1.9
    }
    
    maintenance_calories = bmr * activity_multipliers.get(activity_level, 1.2)
    
    # Adjust based on BMI category and goals
    if bmi_category == "Underweight":
        target_calories = maintenance_calories + 300  # Weight gain
    elif bmi_category == "Overweight" or bmi_category == "Obese":
        target_calories = maintenance_calories - 500  # Weight loss
    else:
        target_calories = maintenance_calories  # Maintenance
    
    return {
        'bmr': round(bmr),
        'maintenance': round(maintenance_calories),
        'target': round(target_calories),
        'goal': 'gain' if bmi_category == "Underweight" else 'lose' if bmi_category in ["Overweight", "Obese"] else 'maintain'
    }

def calculate_bmr(weight, height, age, gender):
    """Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation
    
    Args:
        weight: Weight in kg
        height: Height in cm
        age: Age in years
        gender: Gender ('M', 'F', 'O', or 'P')
    
    Returns:
        BMR value as integer
    """
    try:
        # Default to female if gender not specified
        if gender == 'M':
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:  # Female or Other (default to female formula)
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
        
        return round(bmr)
    except (TypeError, ValueError):
        return 0

def get_health_tips(bmi_category):
    """Get personalized health tips based on BMI category"""
    tips = {
        "Underweight": [
            "Focus on nutrient-dense foods rather than empty calories",
            "Eat frequent, smaller meals throughout the day",
            "Include healthy fats like nuts, seeds, and avocado",
            "Strength training can help build muscle mass",
            "Consider protein shakes between meals",
            "Get enough sleep and manage stress levels",
            "Consult a healthcare provider if struggling to gain weight"
        ],
        "Normal weight": [
            "Maintain your healthy habits with balanced nutrition",
            "Include variety in your diet for complete nutrition",
            "Regular exercise supports overall health",
            "Stay hydrated and listen to your body's hunger cues",
            "Get regular health check-ups",
            "Focus on maintaining muscle mass with strength training",
            "Practice mindful eating habits"
        ],
        "Overweight": [
            "Focus on portion control and mindful eating",
            "Increase physical activity gradually",
            "Choose whole foods over processed options",
            "Stay consistent with healthy habits",
            "Set realistic, achievable goals",
            "Include more fiber-rich foods for satiety",
            "Track your progress but don't obsess over the scale"
        ],
        "Obese": [
            "Consult with healthcare providers for personalized plan",
            "Start with small, sustainable changes",
            "Focus on building healthy habits rather than quick fixes",
            "Incorporate both diet and exercise changes",
            "Seek support from professionals or support groups",
            "Focus on non-scale victories like increased energy",
            "Be patient and kind to yourself throughout the journey"
        ]
    }
    
    return tips.get(bmi_category, ["Maintain a balanced diet and regular exercise."])

def validate_health_data(height, weight, age=None):
    """Validate health input data"""
    errors = []
    
    if not height or height < 50 or height > 250:
        errors.append("Height should be between 50cm and 250cm")
    
    if not weight or weight < 20 or weight > 300:
        errors.append("Weight should be between 20kg and 300kg")
    
    if age and (age < 1 or age > 120):
        errors.append("Age should be between 1 and 120 years")
    
    return errors

def generate_meal_suggestions(bmi_category, user_profile=None, meal_types=None):
    """Generate meal suggestions based on BMI category and user preferences
    
    Args:
        bmi_category (str): The BMI category ('Underweight', 'Normal weight', etc.)
        user_profile (UserProfile, optional): User profile for preferences
        meal_types (list, optional): List of specific meal types to generate ('breakfast', 'lunch', etc.)
    
    Returns:
        list: List of meal suggestions with nutritional information

    """

    # Base meal templates
    meal_templates = {
        "Underweight": {
            'breakfast': {
                'meal_type': 'breakfast',
                'name': 'High-Protein Oatmeal',
                'description': 'Nutrient-dense oatmeal with protein boost for healthy weight gain',
                'calories': 450,
                'protein': 20,
                'carbs': 65,
                'fats': 12,
                'ingredients': '1/2 cup oats, 1 cup whole milk, 1 scoop protein powder, 1 banana, 2 tbsp mixed nuts, 1 tsp honey',
                'preparation': 'Cook oats with milk, stir in protein powder, top with banana slices, nuts, and drizzle with honey. Serve warm.'
            },
            'lunch': {
                'meal_type': 'lunch',
                'name': 'Chicken Avocado Wrap',
                'description': 'Protein-packed wrap with healthy fats for sustained energy',
                'calories': 520,
                'protein': 35,
                'carbs': 45,
                'fats': 22,
                'ingredients': 'Whole wheat wrap, 150g grilled chicken, 1/2 avocado, 1 slice cheese, lettuce, tomato, 1 tbsp Greek yogurt dressing',
                'preparation': 'Warm the wrap, layer with sliced chicken, avocado, cheese, and fresh vegetables. Add dressing and roll tightly.'
            },
            'dinner': {
                'meal_type': 'dinner',
                'name': 'Salmon with Sweet Potato & Greens',
                'description': 'Omega-3 rich meal for muscle recovery and healthy weight gain',
                'calories': 580,
                'protein': 40,
                'carbs': 55,
                'fats': 25,
                'ingredients': '200g salmon fillet, 1 medium sweet potato, 2 cups mixed greens, 1 tbsp olive oil, lemon wedges, herbs',
                'preparation': 'Bake salmon with herbs at 200°C for 15-20 minutes. Roast sweet potato cubes. Serve with steamed greens.'
            }
        },
        "Normal weight": {
            'breakfast': {
                'meal_type': 'breakfast',
                'name': 'Balanced Smoothie Bowl',
                'description': 'Nutrient-rich smoothie bowl for sustained energy and maintenance',
                'calories': 380,
                'protein': 15,
                'carbs': 55,
                'fats': 12,
                'ingredients': '1/2 cup Greek yogurt, 1/2 cup mixed berries, 1/2 banana, 1/4 cup granola, 1 tsp chia seeds, 1 tsp honey',
                'preparation': 'Blend yogurt and fruits until smooth, pour into bowl, top with granola and chia seeds. Drizzle with honey.'
            },
            'lunch': {
                'meal_type': 'lunch',
                'name': 'Quinoa Salad Bowl',
                'description': 'Balanced plant-based protein bowl with complete nutrients',
                'calories': 420,
                'protein': 18,
                'carbs': 60,
                'fats': 15,
                'ingredients': '1 cup cooked quinoa, 1/2 cup chickpeas, mixed vegetables (cucumber, bell peppers, cherry tomatoes), 1 tbsp olive oil, lemon juice, fresh herbs',
                'preparation': 'Mix cooked quinoa with chickpeas and chopped vegetables. Dress with olive oil, lemon juice, and fresh herbs. Chill before serving.'
            },
            'dinner': {
                'meal_type': 'dinner',
                'name': 'Turkey & Vegetable Stir-fry',
                'description': 'Lean protein with colorful vegetables for balanced nutrition',
                'calories': 450,
                'protein': 35,
                'carbs': 40,
                'fats': 18,
                'ingredients': '150g ground turkey, 2 cups mixed vegetables (broccoli, carrots, snap peas), 1 tbsp soy sauce, 1 tsp sesame oil, garlic, ginger',
                'preparation': 'Stir-fry turkey until cooked, add vegetables and seasonings. Cook until vegetables are tender-crisp. Serve with brown rice.'
            }
        },
        "Overweight": {
            'breakfast': {
                'meal_type': 'breakfast',
                'name': 'Vegetable Egg Scramble',
                'description': 'High-protein, low-carb breakfast to support weight management',
                'calories': 320,
                'protein': 25,
                'carbs': 15,
                'fats': 18,
                'ingredients': '3 eggs, 1 cup spinach, 1/2 cup mushrooms, 1/4 cup tomatoes, 1 tsp olive oil, herbs, 1 slice whole grain toast',
                'preparation': 'Sauté vegetables in olive oil, add beaten eggs and scramble until cooked. Season with herbs and pepper. Serve with toast.'
            },
            'lunch': {
                'meal_type': 'lunch',
                'name': 'Grilled Chicken Salad',
                'description': 'Lean protein salad with fiber-rich vegetables for satiety',
                'calories': 350,
                'protein': 30,
                'carbs': 20,
                'fats': 15,
                'ingredients': '150g grilled chicken breast, 3 cups mixed greens, 1 cup vegetables (cucumber, bell peppers, carrots), 1 tbsp light vinaigrette',
                'preparation': 'Grill chicken until cooked through. Chop vegetables and mix with greens. Top with sliced chicken and light dressing.'
            },
            'dinner': {
                'meal_type': 'dinner',
                'name': 'Baked Fish with Roasted Vegetables',
                'description': 'Low-calorie, high-protein dinner for weight management',
                'calories': 380,
                'protein': 35,
                'carbs': 25,
                'fats': 12,
                'ingredients': '200g white fish (cod or tilapia), 2 cups mixed vegetables (zucchini, bell peppers, onions), 1 tsp olive oil, lemon, herbs',
                'preparation': 'Season fish with herbs and bake at 180°C for 15-20 minutes. Roast vegetables with olive oil. Serve with lemon wedges.'
            }
        },
        "Obese": {
            'breakfast': {
                'meal_type': 'breakfast',
                'name': 'High-Fiber Protein Shake',
                'description': 'Low-calorie, high-satiety shake for weight loss',
                'calories': 280,
                'protein': 25,
                'carbs': 25,
                'fats': 8,
                'ingredients': '1 scoop protein powder, 1 cup unsweetened almond milk, 1 tbsp flax seeds, 1/2 cup berries, handful spinach, ice',
                'preparation': 'Blend all ingredients until smooth. Add more ice for thicker consistency. Drink immediately.'
            },
            'lunch': {
                'meal_type': 'lunch',
                'name': 'Lean Protein & Vegetable Soup',
                'description': 'Large volume soup with lean protein for maximum satiety',
                'calories': 300,
                'protein': 35,
                'carbs': 15,
                'fats': 12,
                'ingredients': '150g shredded chicken breast, 4 cups vegetable broth, 3 cups mixed vegetables (celery, carrots, cabbage), herbs, spices',
                'preparation': 'Simmer vegetables in broth until tender. Add shredded chicken and seasonings. Cook for additional 10 minutes.'
            },
            'dinner': {
                'meal_type': 'dinner',
                'name': 'Turkey Meatballs with Zucchini Noodles',
                'description': 'Low-carb, high-protein alternative to pasta',
                'calories': 320,
                'protein': 40,
                'carbs': 12,
                'fats': 10,
                'ingredients': '200g ground turkey, 2 medium zucchinis, 1/2 cup marinara sauce, herbs, garlic, 1 tbsp olive oil',
                'preparation': 'Form turkey into meatballs and bake at 200°C for 20 minutes. Spiralize zucchini into noodles and sauté briefly. Combine with sauce.'
            }
        }
    }
    
    # Get meals for the specific BMI category
    meals = meal_templates.get(bmi_category, meal_templates["Normal weight"])
    
    # Convert to list format for the model
    meal_list = []
    for meal_type, meal_data in meals.items():
        meal_list.append(meal_data)
    
    return meal_list

def calculate_water_intake(weight_kg):
    """Calculate recommended daily water intake in liters"""
    # General guideline: 30-35 ml per kg of body weight
    return round((weight_kg * 0.033), 2)

def get_ideal_weight_range(height_cm, gender):
    """Calculate ideal weight range based on height and gender"""
    height_m = height_cm / 100
    # BMI range for healthy weight: 18.5 - 24.9
    min_weight = 18.5 * (height_m ** 2)
    max_weight = 24.9 * (height_m ** 2)
    
    return {
        'min': round(min_weight, 1),
        'max': round(max_weight, 1)
    }

def calculate_macronutrients(calories, goal='maintain'):
    """Calculate recommended macronutrient distribution"""
    if goal == 'weight_loss':
        # Higher protein, moderate fat, lower carbs
        protein_ratio = 0.35
        fat_ratio = 0.30
        carb_ratio = 0.35
    elif goal == 'muscle_gain':
        # Higher protein and carbs, moderate fat
        protein_ratio = 0.30
        fat_ratio = 0.25
        carb_ratio = 0.45
    else:  # maintain
        # Balanced distribution
        protein_ratio = 0.25
        fat_ratio = 0.25
        carb_ratio = 0.50
    
    # Calculate grams (protein & carbs: 4 cal/g, fat: 9 cal/g)
    protein_cals = calories * protein_ratio
    fat_cals = calories * fat_ratio
    carb_cals = calories * carb_ratio
    
    return {
        'protein_grams': round(protein_cals / 4),
        'fat_grams': round(fat_cals / 9),
        'carb_grams': round(carb_cals / 4),
        'protein_percent': int(protein_ratio * 100),
        'fat_percent': int(fat_ratio * 100),
        'carb_percent': int(carb_ratio * 100)
    }

def get_activity_multiplier(activity_level):
    """Get the activity multiplier for calorie calculations"""
    multipliers = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'very_active': 1.9
    }
    return multipliers.get(activity_level, 1.2)

def generate_workout_recommendation(bmi_category, activity_level):
    """Generate workout recommendations based on BMI and activity level"""
    recommendations = {
        "Underweight": {
            'focus': 'Strength training and muscle building',
            'frequency': '3-4 times per week',
            'workouts': [
                'Compound exercises (squats, deadlifts, bench press)',
                'Progressive overload training',
                'Adequate rest between sessions',
                'Yoga for flexibility and mindfulness'
            ],
            'cardio': 'Light cardio 2-3 times per week (20-30 minutes)',
            'tips': 'Focus on form, eat protein-rich meals post-workout'
        },
        "Normal weight": {
            'focus': 'Maintenance and overall fitness',
            'frequency': '4-5 times per week',
            'workouts': [
                'Balanced strength training',
                'HIIT workouts for cardiovascular health',
                'Flexibility and mobility exercises',
                'Sports and recreational activities'
            ],
            'cardio': 'Moderate cardio 3-4 times per week (30-45 minutes)',
            'tips': 'Mix up routines to prevent plateaus'
        },
        "Overweight": {
            'focus': 'Fat loss and cardiovascular health',
            'frequency': '5-6 times per week',
            'workouts': [
                'Full-body circuit training',
                'Low-impact cardio (swimming, cycling)',
                'Strength training with moderate weights',
                'Bodyweight exercises'
            ],
            'cardio': 'Daily moderate cardio (45-60 minutes)',
            'tips': 'Start slow, focus on consistency over intensity'
        },
        "Obese": {
            'focus': 'Safe weight loss and mobility',
            'frequency': 'Daily light activity',
            'workouts': [
                'Walking program (gradually increase distance)',
                'Chair exercises and light stretching',
                'Water aerobics or swimming',
                'Physical therapy recommended exercises'
            ],
            'cardio': 'Daily walking (start with 10-15 minutes, build up)',
            'tips': 'Consult healthcare provider before starting, focus on non-weight bearing exercises'
        }
    }
    
    return recommendations.get(bmi_category, recommendations["Normal weight"])

def calculate_progress_score(current_bmi, previous_bmi=None, goal=None):
    """Calculate a progress score based on BMI changes and goals"""
    if previous_bmi is None:
        return 50  # Default starting score
    
    healthy_range_min = 18.5
    healthy_range_max = 24.9
    
    # Calculate distance from healthy range
    if current_bmi < healthy_range_min:
        distance_from_healthy = healthy_range_min - current_bmi
    elif current_bmi > healthy_range_max:
        distance_from_healthy = current_bmi - healthy_range_max
    else:
        distance_from_healthy = 0
    
    # Calculate improvement
    bmi_change = previous_bmi - current_bmi
    
    # Score calculation (simplified)
    base_score = 50
    improvement_bonus = bmi_change * 10  # Positive change increases score
    healthy_bonus = 30 if distance_from_healthy == 0 else 0
    
    final_score = base_score + improvement_bonus + healthy_bonus
    
    # Ensure score stays within 0-100 range
    return max(0, min(100, final_score))

def generate_nutrition_response(user_message: str, bmi_category: str = None) -> str:
    """Generate AI response for nutrition queries"""
    message_lower = user_message.lower()
    
    # Common nutrition-related keywords and their responses
    responses = {
        'calories': {
            'default': "A balanced diet is key to managing calories. The average daily needs are 2000-2500 calories, but this varies based on factors like age, gender, and activity level.",
            'underweight': "Focus on increasing your caloric intake with nutrient-dense foods. Aim for 300-500 calories above your maintenance level.",
            'normal': "Maintain your current caloric intake if it's working well for you. Focus on food quality and regular meals.",
            'overweight': "Consider a moderate calorie deficit of 500 calories per day for sustainable weight loss.",
            'obese': "Work with a healthcare provider to develop a safe calorie-reduction plan."
        },
        'protein': {
            'default': "Protein is essential for building and repairing tissues. Good sources include lean meats, fish, eggs, legumes, and dairy.",
            'underweight': "Increase protein intake to support muscle growth. Aim for 1.6-2.2g of protein per kg of body weight.",
            'normal': "Maintain a protein intake of 0.8-1.2g per kg of body weight for general health.",
            'overweight': "Include lean protein sources to help preserve muscle mass during weight loss.",
            'obese': "Focus on lean protein sources to support metabolism and satiety."
        },
        'exercise': {
            'default': "Regular physical activity is important for overall health. Aim for at least 150 minutes of moderate activity per week.",
            'underweight': "Focus on strength training to build muscle mass, with moderate cardio.",
            'normal': "Maintain a balanced mix of cardio and strength training.",
            'overweight': "Start with low-impact activities and gradually increase intensity.",
            'obese': "Begin with gentle activities like walking and water exercises."
        }
    }

    # Check if message contains specific keywords
    response = None
    for keyword, category_responses in responses.items():
        if keyword in message_lower:
            if bmi_category and bmi_category.lower().replace(' ', '') in category_responses:
                response = category_responses[bmi_category.lower().replace(' ', '')]
            else:
                response = category_responses['default']
            break

    # If no specific keyword found, provide a general response
    if not response:
        response = (
            "I can help you with nutrition advice! Ask me about:\n"
            "- Calorie needs and meal planning\n"
            "- Protein and nutrient recommendations\n"
            "- Exercise and physical activity\n"
            "- BMI and weight management\n"
            "What would you like to know?"
        )

    return response

def get_nutrition_advice(bmi_category, health_goal):
    """Get personalized nutrition advice based on BMI and goals"""
    advice_templates = {
        "Underweight": {
            "weight_loss": "Focus on building healthy weight through muscle mass rather than fat",
            "maintain": "Maintain your current healthy habits while ensuring adequate nutrition",
            "muscle_gain": "Perfect! Focus on calorie surplus with quality protein and strength training",
            "improve_health": "Ensure you're getting all essential nutrients for optimal health"
        },
        "Normal weight": {
            "weight_loss": "Focus on body recomposition - losing fat while maintaining muscle",
            "maintain": "Excellent! Continue your balanced diet and regular exercise routine",
            "muscle_gain": "Focus on slight calorie surplus with increased protein intake",
            "improve_health": "Optimize your nutrition with variety and whole foods"
        },
        "Overweight": {
            "weight_loss": "Create a sustainable calorie deficit with nutrient-dense foods",
            "maintain": "Work on maintaining current weight while improving body composition",
            "muscle_gain": "Focus on body recomposition - build muscle while losing fat",
            "improve_health": "Prioritize whole foods and regular physical activity"
        },
        "Obese": {
            "weight_loss": "Start with small, sustainable changes and gradual weight loss",
            "maintain": "Focus on maintaining current weight while building healthy habits",
            "muscle_gain": "Prioritize weight loss first, then focus on muscle building",
            "improve_health": "Small consistent changes will lead to significant health improvements"
        }
    }
    
    return advice_templates.get(bmi_category, {}).get(health_goal, "Focus on balanced nutrition and regular physical activity.")