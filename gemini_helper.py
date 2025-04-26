import os
import logging
import json
from flask import current_app
from google.generativeai import GenerativeModel
import google.generativeai as genai

def initialize_gemini():
    """Initialize the Gemini API with the API key."""
    api_key = os.environ.get("GEMINI_API_KEY") or current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        logging.warning("No Gemini API key found. Analysis features will not work.")
        return None
    
    genai.configure(api_key=api_key)
    
    # Get available models for debugging
    try:
        models = genai.list_models()
        logging.info(f"Available Gemini models: {[model.name for model in models]}")
    except Exception as e:
        logging.warning(f"Could not list available models: {str(e)}")
    
    return genai

def analyze_blood_sugar_report(report_text, user_info):
    """
    Analyze blood sugar report using Gemini API.
    
    Args:
        report_text (str): Extracted text from blood sugar report PDF
        user_info (dict): User information for context
        
    Returns:
        dict: Analysis results including insights and recommendations
    """
    genai_client = initialize_gemini()
    if not genai_client:
        return {
            "success": False,
            "message": "Gemini API not configured. Please set the API key.",
            "insights": [],
            "recommendations": []
        }
    
    try:
        # Format user context
        user_context = (
            f"Patient Information:\n"
            f"- Age: {user_info.get('age', 'Unknown')}\n"
            f"- Gender: {user_info.get('gender', 'Unknown')}\n"
            f"- Diabetes Type: {user_info.get('diabetes_type', 'Unknown')}\n"
            f"- Height: {user_info.get('height', 'Unknown')} cm\n"
            f"- Weight: {user_info.get('weight', 'Unknown')} kg\n"
            f"- BMI: {user_info.get('bmi', 'Unknown')}\n"
            f"- Ethnicity: {user_info.get('ethnicity', 'Unknown')}\n"
            f"- Diagnosed Date: {user_info.get('diagnosed_date', 'Unknown')}\n"
        )
        
        # Create the prompt for Gemini
        prompt = f"""
        You are a medical AI assistant specializing in diabetes management. 
        
        Analyze the following blood sugar report and provide:
        1. Key insights about the patient's blood sugar levels
        2. Trends or patterns in the data
        3. Potential concerns or issues to address
        4. Specific diet recommendations based on the patient's ethnicity and condition
        5. Exercise recommendations suitable for the patient
        
        {user_context}
        
        Blood Sugar Report:
        {report_text}
        
        Format your response as JSON with the following structure:
        {{
            "insights": [
                {{
                    "title": "short title",
                    "description": "detailed explanation"
                }}
            ],
            "trends": [
                {{
                    "title": "short title",
                    "description": "detailed explanation"
                }}
            ],
            "concerns": [
                {{
                    "title": "short title",
                    "description": "detailed explanation",
                    "severity": "low|medium|high"
                }}
            ],
            "diet_recommendations": [
                {{
                    "title": "short title",
                    "description": "detailed explanation",
                    "foods_to_include": ["food1", "food2"],
                    "foods_to_avoid": ["food1", "food2"]
                }}
            ],
            "exercise_recommendations": [
                {{
                    "title": "short title",
                    "description": "detailed explanation",
                    "duration": "recommended duration",
                    "frequency": "recommended frequency",
                    "intensity": "low|medium|high"
                }}
            ]
        }}
        """
        
        # Generate content with Gemini - directly using a model that works
        try:
            model = GenerativeModel("gemini-1.5-flash")
            logging.info("Using model: gemini-1.5-flash")
        except Exception:
            try:
                model = GenerativeModel("gemini-2.0-flash")
                logging.info("Using model: gemini-2.0-flash")
            except Exception:
                model = GenerativeModel("models/gemini-2.0-pro-exp")
                logging.info("Using model: models/gemini-2.0-pro-exp")
                
        response = model.generate_content(prompt)
        
        # Process and return the analysis
        return {
            "success": True,
            "analysis": response.text,
            "message": "Analysis completed successfully."
        }
    
    except Exception as e:
        logging.error(f"Error in Gemini API analysis: {str(e)}")
        return {
            "success": False,
            "message": f"Error analyzing report: {str(e)}",
            "insights": [],
            "recommendations": []
        }

def generate_diet_plan(user_info, blood_sugar_data):
    """
    Generate a personalized diet plan based on user information and blood sugar data.
    
    Args:
        user_info (dict): User information
        blood_sugar_data (list): Recent blood sugar readings
        
    Returns:
        dict: Diet plan with meals and recommendations
    """
    genai_client = initialize_gemini()
    if not genai_client:
        return {
            "success": False,
            "message": "Gemini API not configured. Please set the API key.",
            "diet_plan": {}
        }
    
    try:
        # Format blood sugar data
        blood_sugar_summary = "\n".join([
            f"- {entry.get('date')}: {entry.get('value')} mg/dL ({entry.get('meal_status', 'unknown')})"
            for entry in blood_sugar_data[:10]  # Last 10 entries
        ])
        
        # Create the prompt for Gemini
        prompt = f"""
        You are a nutritionist specializing in diabetes management. 
        
        Create a personalized 7-day diet plan for a patient with the following profile:
        - Age: {user_info.get('age', 'Unknown')}
        - Gender: {user_info.get('gender', 'Unknown')}
        - Diabetes Type: {user_info.get('diabetes_type', 'Unknown')}
        - Height: {user_info.get('height', 'Unknown')} cm
        - Weight: {user_info.get('weight', 'Unknown')} kg
        - BMI: {user_info.get('bmi', 'Unknown')}
        - Ethnicity: {user_info.get('ethnicity', 'Unknown')}
        
        Recent blood sugar readings:
        {blood_sugar_summary}
        
        The diet plan should:
        1. Be culturally appropriate considering the patient's ethnicity
        2. Help regulate blood sugar levels
        3. Support weight management if needed
        4. Include nutritional information (calories, carbs, proteins, fats)
        
        Format your response as JSON with the following structure:
        {{
            "title": "Diet Plan Title",
            "description": "Overview of the diet plan",
            "calories": daily_calorie_target,
            "carbs": daily_carbs_target_in_grams,
            "proteins": daily_proteins_target_in_grams,
            "fats": daily_fats_target_in_grams,
            "days": [
                {{
                    "day": "Day 1",
                    "meals": [
                        {{
                            "name": "Breakfast",
                            "time": "8:00 AM",
                            "description": "Detailed meal description",
                            "foods": ["food1", "food2"],
                            "calories": calories_in_meal,
                            "carbs": carbs_in_grams,
                            "proteins": proteins_in_grams,
                            "fats": fats_in_grams
                        }},
                        // Add lunch, dinner, snacks
                    ]
                }},
                // Continue with days 2-7
            ],
            "general_guidelines": [
                "guideline 1",
                "guideline 2"
            ],
            "foods_to_avoid": [
                "food1",
                "food2"
            ]
        }}
        """
        
        # Generate content with Gemini - directly using a model that works
        try:
            model = GenerativeModel("gemini-1.5-flash")
            logging.info("Using model: gemini-1.5-flash for diet plan")
        except Exception:
            try:
                model = GenerativeModel("gemini-2.0-flash")
                logging.info("Using model: gemini-2.0-flash for diet plan")
            except Exception:
                model = GenerativeModel("models/gemini-2.0-pro-exp")
                logging.info("Using model: models/gemini-2.0-pro-exp for diet plan")
            
        response = model.generate_content(prompt)
        
        # Process and return the diet plan
        return {
            "success": True,
            "diet_plan": response.text,
            "message": "Diet plan generated successfully."
        }
    
    except Exception as e:
        logging.error(f"Error generating diet plan: {str(e)}")
        return {
            "success": False,
            "message": f"Error generating diet plan: {str(e)}",
            "diet_plan": {}
        }

def generate_exercise_plan(user_info, medical_records=None):
    """
    Generate a personalized exercise plan based on user information and medical records.
    
    Args:
        user_info (dict): User information
        medical_records (list): Optional medical records for context
        
    Returns:
        dict: Exercise plan with activities and recommendations
    """
    genai_client = initialize_gemini()
    if not genai_client:
        return {
            "success": False,
            "message": "Gemini API not configured. Please set the API key.",
            "exercise_plan": {}
        }
    
    try:
        # Create medical records context if available
        medical_context = ""
        if medical_records:
            medical_context = "Medical Records:\n" + "\n".join([
                f"- {record.get('record_type')}: {record.get('notes', 'No notes')}"
                for record in medical_records[:5]  # Last 5 records
            ])
        
        # Create the prompt for Gemini
        prompt = f"""
        You are a certified fitness trainer specializing in exercise programs for people with diabetes.
        
        Create a personalized weekly exercise plan for a patient with the following profile:
        - Age: {user_info.get('age', 'Unknown')}
        - Gender: {user_info.get('gender', 'Unknown')}
        - Diabetes Type: {user_info.get('diabetes_type', 'Unknown')}
        - Height: {user_info.get('height', 'Unknown')} cm
        - Weight: {user_info.get('weight', 'Unknown')} kg
        - BMI: {user_info.get('bmi', 'Unknown')}
        
        {medical_context}
        
        The exercise plan should:
        1. Be suitable for someone with diabetes
        2. Include a mix of cardiovascular, strength, and flexibility exercises
        3. Start at an appropriate level based on the patient's likely fitness level
        4. Include progression options for each exercise
        5. Specify duration, intensity, and frequency
        
        Format your response as JSON with the following structure:
        {{
            "title": "Exercise Plan Title",
            "description": "Overview of the exercise plan",
            "weekly_schedule": [
                {{
                    "day": "Monday",
                    "focus": "main focus (e.g., Cardio, Strength)",
                    "exercises": [
                        {{
                            "name": "Exercise name",
                            "duration": "duration in minutes",
                            "intensity": "low|medium|high",
                            "description": "Detailed description of how to perform",
                            "benefits": "benefits for diabetes management",
                            "calories_burned": estimated_calories,
                            "progression": "how to make it more challenging over time"
                        }},
                        // Additional exercises
                    ]
                }},
                // Continue with other days of the week
            ],
            "safety_guidelines": [
                "guideline 1",
                "guideline 2"
            ],
            "blood_sugar_monitoring": "advice on monitoring blood sugar before/during/after exercise"
        }}
        """
        
        # Generate content with Gemini - directly using a model that works
        try:
            model = GenerativeModel("gemini-1.5-flash")
            logging.info("Using model: gemini-1.5-flash for exercise plan")
        except Exception:
            try:
                model = GenerativeModel("gemini-2.0-flash")
                logging.info("Using model: gemini-2.0-flash for exercise plan")
            except Exception:
                model = GenerativeModel("models/gemini-2.0-pro-exp")
                logging.info("Using model: models/gemini-2.0-pro-exp for exercise plan")
            
        response = model.generate_content(prompt)
        
        # Process and return the exercise plan
        return {
            "success": True,
            "exercise_plan": response.text,
            "message": "Exercise plan generated successfully."
        }
    
    except Exception as e:
        logging.error(f"Error generating exercise plan: {str(e)}")
        return {
            "success": False,
            "message": f"Error generating exercise plan: {str(e)}",
            "exercise_plan": {}
        }
