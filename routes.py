import os
import json
import logging
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import PyPDF2

from app import app, db
from models import User, BloodSugarEntry, MedicalRecord, DietPlan, Meal, ExercisePlan, Exercise, Medication, ReportAnalysis, Questionnaire
from utils import allowed_file, save_uploaded_file, extract_text_from_pdf, get_progress_metrics, group_entries_by_date
from gemini_helper import analyze_blood_sugar_report, generate_diet_plan, generate_exercise_plan

def clean_and_parse_analysis_result(raw_result):
    import json
    import re

    if not raw_result or not isinstance(raw_result, str):
        return {}

    try:
        # Remove all Markdown backticks and 'json' prefix
        cleaned = re.sub(r'^```json|```$', '', raw_result, flags=re.IGNORECASE | re.MULTILINE)
        cleaned = cleaned.strip()
        
        # Remove residual escape characters
        cleaned = bytes(cleaned, "utf-8").decode("unicode_escape")
        
        # Ensure the string starts with '{' and ends with '}'
        start_idx = cleaned.find('{')
        end_idx = cleaned.rfind('}') + 1
        cleaned = cleaned[start_idx:end_idx]

        return json.loads(cleaned)

    except json.JSONDecodeError as e:
        logging.error(f"JSON Parsing Failed: {e}\nCleaned JSON:\n{cleaned}")
        return {}
    except Exception as e:
        logging.error(f"Unexpected Error: {e}")
        return {}


# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already registered', 'danger')
            return render_template('register.html')
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    latest_analysis = ReportAnalysis.query.filter_by(user_id=current_user.id).order_by(ReportAnalysis.created_at.desc()).first()
    analysis_data = {}

    if latest_analysis:
        analysis_data = clean_and_parse_analysis_result(latest_analysis.analysis_result)
        # Ensure keys exist
        analysis_data.setdefault('insights', [])
        analysis_data.setdefault('trends', [])
        analysis_data.setdefault('concerns', [])

    return render_template("dashboard.html", analysis_data=analysis_data)

# Profile routes
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.age = request.form.get('age', type=int)
        current_user.gender = request.form.get('gender')
        current_user.height = request.form.get('height', type=float)
        current_user.weight = request.form.get('weight', type=float)
        current_user.diabetes_type = request.form.get('diabetes_type')
        current_user.ethnicity = request.form.get('ethnicity')
        
        diagnosed_date = request.form.get('diagnosed_date')
        if diagnosed_date:
            current_user.diagnosed_date = datetime.strptime(diagnosed_date, '%Y-%m-%d')
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html')

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_user.check_password(current_password):
        flash('Current password is incorrect', 'danger')
        return redirect(url_for('profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'danger')
        return redirect(url_for('profile'))
    
    current_user.set_password(new_password)
    db.session.commit()
    flash('Password changed successfully', 'success')
    return redirect(url_for('profile'))

# Medication routes
@app.route('/medications')
@login_required
def medications():
    # Get latest questionnaire entry
    latest_questionnaire = Questionnaire.query.filter_by(
        user_id=current_user.id
    ).order_by(Questionnaire.created_at.desc()).first()

    medical_conditions = []
    medications_list = []

    if latest_questionnaire:
        if latest_questionnaire.medical_conditions:
            medical_conditions = latest_questionnaire.medical_conditions.split(',')
        if latest_questionnaire.medications_list:
            medications_list = latest_questionnaire.medications_list.split(',')

    return render_template(
        'medications.html',
        medical_conditions=medical_conditions,
        medications_list=medications_list
    )

@app.route('/medications/toggle/<int:medication_id>', methods=['POST'])
@login_required
def toggle_medication(medication_id):
    medication = Medication.query.get_or_404(medication_id)
    
    if medication.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('medications'))
    
    medication.active = not medication.active
    db.session.commit()
    flash(f"Medication {medication.name} {'activated' if medication.active else 'deactivated'}", 'success')
    return redirect(url_for('medications'))

@app.route('/medications/delete/<int:medication_id>', methods=['POST'])
@login_required
def delete_medication(medication_id):
    medication = Medication.query.get_or_404(medication_id)
    
    if medication.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('medications'))
    
    db.session.delete(medication)
    db.session.commit()
    flash('Medication deleted', 'success')
    return redirect(url_for('medications'))

# Upload and analysis routes
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        report_file = request.files.get('report')
        
        if not report_file or not report_file.filename:
            flash('No file selected', 'danger')
            return redirect(url_for('upload'))
        
        if not allowed_file(report_file.filename):
            flash('Invalid file type. Only PDF files are allowed.', 'danger')
            return redirect(url_for('upload'))
        
        # Save the uploaded file
        file_path = save_uploaded_file(report_file, subfolder=f"user_{current_user.id}/reports")
        
        if file_path:
            # Extract text from PDF
            report_text = extract_text_from_pdf(file_path)
            
            if not report_text:
                flash('Could not extract text from the PDF', 'warning')
                return redirect(url_for('upload'))
            
            # Prepare user info for analysis
            user_info = {
                'age': current_user.age,
                'gender': current_user.gender,
                'diabetes_type': current_user.diabetes_type,
                'height': current_user.height,
                'weight': current_user.weight,
                'bmi': current_user.get_bmi(),
                'ethnicity': current_user.ethnicity,
                'diagnosed_date': current_user.diagnosed_date
            }
            
            # Analyze report with Gemini
            analysis_result = analyze_blood_sugar_report(report_text, user_info)
            
            if analysis_result['success']:
                # Save analysis to database
                analysis = ReportAnalysis(
                    user_id=current_user.id,
                    file_path=file_path,
                    analysis_result=json.dumps(analysis_result['analysis'])
                )
                db.session.add(analysis)
                db.session.commit()
                
                # Create a new questionnaire linked to this report
                questionnaire = Questionnaire(
                    user_id=current_user.id,
                    report_id=analysis.id,
                    first_name=current_user.first_name,
                    last_name=current_user.last_name,
                    completed=False
                )
                db.session.add(questionnaire)
                db.session.commit()
                
                flash('Report analyzed successfully. Please complete the questionnaire to get personalized recommendations.', 'success')
                # Redirect to questionnaire with the report ID
                return redirect(url_for('questionnaire', report_id=analysis.id))
            else:
                flash(f"Error analyzing report: {analysis_result['message']}", 'danger')
                return redirect(url_for('upload'))
        else:
            flash('Error saving file', 'danger')
            return redirect(url_for('upload'))
    
    return render_template('upload.html')

@app.route('/analysis/<int:analysis_id>')
@login_required
def analysis_results(analysis_id):
    analysis = ReportAnalysis.query.get_or_404(analysis_id)
    
    if analysis.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('dashboard'))
    
    # Parse the analysis result (assuming it's JSON)
    try:
        analysis_data = json.loads(analysis.analysis_result)
    except:
        analysis_data = {"error": "Could not parse analysis result"}
    
    return render_template('analysis_results.html', analysis=analysis, analysis_data=analysis_data)

# Diet plan routes
@app.route('/diet-plan', methods=['GET', 'POST'])
@login_required
def diet_plan():
    diet_plan = DietPlan.query.filter_by(user_id=current_user.id).order_by(DietPlan.created_at.desc()).first()

    if request.method == 'POST':
        latest_analysis = ReportAnalysis.query.filter_by(user_id=current_user.id).order_by(ReportAnalysis.created_at.desc()).first()

        if latest_analysis:
            analysis = clean_and_parse_analysis_result(latest_analysis.analysis_result)
            # Check if recommendations exist
            diet_recommendations = analysis.get("diet_recommendations", [])
            
            if diet_recommendations:
                reco = diet_recommendations[0]
                new_diet_plan = DietPlan(
                    user_id=current_user.id,
                    title=reco.get("title", "AI-Generated Diet Plan"),
                    description=reco.get("description", ""),
                    calories=1800,
                    carbs=200,
                    proteins=80,
                    fats=60
                )
                db.session.add(new_diet_plan)
                db.session.commit()
                flash("New diet plan generated from analysis.", "success")
            else:
                flash("No diet recommendations found in the analysis.", "warning")
            
            return redirect(url_for("diet_plan"))

        else:
            flash("No analysis report found. Please upload a report first.", "warning")
            return redirect(url_for("upload"))

    return render_template("diet_plan.html", diet_plan=diet_plan)


# Exercise plan routes
@app.route('/exercise-plan', methods=['GET', 'POST'])
@login_required
def exercise_plan():
    exercise_plan = ExercisePlan.query.filter_by(user_id=current_user.id).order_by(ExercisePlan.created_at.desc()).first()

    if request.method == 'POST':
        latest_analysis = ReportAnalysis.query.filter_by(user_id=current_user.id).order_by(ReportAnalysis.created_at.desc()).first()

        if latest_analysis:
            analysis = clean_and_parse_analysis_result(latest_analysis.analysis_result)
            # Check if recommendations exist
            exercise_recommendations = analysis.get("exercise_recommendations", [])
            
            if exercise_recommendations:
                reco = exercise_recommendations[0]
                new_exercise_plan = ExercisePlan(
                    user_id=current_user.id,
                    title=reco.get("title", "AI-Generated Exercise Plan"),
                    description=reco.get("description", "")
                )
                db.session.add(new_exercise_plan)
                db.session.commit()
                flash("New exercise plan generated from analysis.", "success")
            else:
                flash("No exercise recommendations found in the analysis.", "warning")
            
            return redirect(url_for("exercise_plan"))

        else:
            flash("No analysis report found. Please upload a report first.", "warning")
            return redirect(url_for("upload"))

    return render_template("exercise_plan.html", exercise_plan=exercise_plan)


# Questionnaire route
@app.route('/questionnaire/<int:report_id>', methods=['GET', 'POST'])
@login_required
def questionnaire(report_id):
    # Get the report and associated questionnaire
    report = ReportAnalysis.query.get_or_404(report_id)
    if report.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get or create questionnaire for this report
    questionnaire = Questionnaire.query.filter_by(report_id=report_id, user_id=current_user.id).first()
    if not questionnaire:
        questionnaire = Questionnaire(
            user_id=current_user.id,
            report_id=report_id,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            completed=False
        )
        db.session.add(questionnaire)
        db.session.commit()
    
    # If questionnaire is already completed, redirect to the analysis results
    if questionnaire.completed:
        flash('You have already completed this questionnaire', 'info')
        return redirect(url_for('analysis_results', analysis_id=report_id))
    
    if request.method == 'POST':
        try:
            # Update user profile information
            current_user.first_name = request.form.get('first_name', current_user.first_name)
            current_user.last_name = request.form.get('last_name', current_user.last_name)
            current_user.age = request.form.get('age', type=int, default=current_user.age)
            current_user.gender = request.form.get('gender', current_user.gender)
            current_user.height = request.form.get('height', type=float, default=current_user.height)
            current_user.weight = request.form.get('weight', type=float, default=current_user.weight)
            current_user.diabetes_type = request.form.get('diabetes_type', current_user.diabetes_type)
            current_user.ethnicity = request.form.get('ethnicity', current_user.ethnicity)
            
            diagnosed_date = request.form.get('diagnosed_date')
            if diagnosed_date:
                current_user.diagnosed_date = datetime.strptime(diagnosed_date, '%Y-%m-%d').date()
            
            # Update questionnaire specific fields
            questionnaire.first_name = request.form.get('first_name', questionnaire.first_name)
            questionnaire.last_name = request.form.get('last_name', questionnaire.last_name)
            questionnaire.activity_level = request.form.get('activity_level')
            questionnaire.occupation_type = request.form.get('occupation_type')
            questionnaire.dietary_restrictions = ','.join(request.form.getlist('dietary_restrictions'))
            questionnaire.medical_conditions = ','.join(request.form.getlist('medical_conditions'))
            questionnaire.medications_list = ','.join(request.form.getlist('medications'))
            questionnaire.other_medications = request.form.get('other_medications')
            questionnaire.allergies = request.form.get('allergies')
            questionnaire.additional_info = request.form.get('additional_info')
            questionnaire.completed = True
            
            # Process medications
            medications = request.form.getlist('medications')
            for med in medications:
                if med and not Medication.query.filter_by(user_id=current_user.id, name=med).first():
                    medication = Medication(
                        user_id=current_user.id,
                        name=med,
                        active=True
                    )
                    db.session.add(medication)
            
            # Save to database
            db.session.commit()
            
            # Generate personalized diet and exercise plans based on completed questionnaire data
            # Prepare user info with updated questionnaire data
            user_info = {
                'age': current_user.age,
                'gender': current_user.gender,
                'diabetes_type': current_user.diabetes_type,
                'height': current_user.height,
                'weight': current_user.weight,
                'bmi': current_user.get_bmi(),
                'ethnicity': current_user.ethnicity,
                'activity_level': questionnaire.activity_level,
                'occupation_type': questionnaire.occupation_type,
                'dietary_restrictions': questionnaire.dietary_restrictions.split(',') if questionnaire.dietary_restrictions else [],
                'medical_conditions': questionnaire.medical_conditions.split(',') if questionnaire.medical_conditions else [],
                'medications': questionnaire.medications_list.split(',') if questionnaire.medications_list else [],
                'allergies': questionnaire.allergies
            }
            
            # Generate diet plan
            try:
                blood_sugar_data = []
                recent_entries = BloodSugarEntry.query.filter_by(user_id=current_user.id).order_by(BloodSugarEntry.measured_at.desc()).limit(10).all()
                for entry in recent_entries:
                    blood_sugar_data.append({
                        'date': entry.measured_at.strftime('%Y-%m-%d %H:%M'),
                        'value': entry.value,
                        'meal_status': entry.meal_status
                    })
                
                diet_result = generate_diet_plan(user_info, blood_sugar_data)
                if diet_result['success']:
                    diet_data = json.loads(diet_result['diet_plan'])
                    
                    new_diet_plan = DietPlan(
                        user_id=current_user.id,
                        title=f"Personalized Diet Plan for {current_user.first_name}",
                        description=diet_data.get('description', 'Based on your blood sugar levels and lifestyle'),
                        calories=diet_data.get('calories', 0),
                        carbs=diet_data.get('carbs', 0),
                        proteins=diet_data.get('proteins', 0),
                        fats=diet_data.get('fats', 0)
                    )
                    db.session.add(new_diet_plan)
                    db.session.commit()
                    
                    # Add meals
                    for meal_data in diet_data.get('meals', []):
                        meal = Meal(
                            diet_plan_id=new_diet_plan.id,
                            name=meal_data.get('name', ''),
                            time=meal_data.get('type', ''),
                            description=meal_data.get('description', ''),
                            calories=meal_data.get('calories', 0),
                            carbs=meal_data.get('carbs', 0),
                            proteins=meal_data.get('proteins', 0),
                            fats=meal_data.get('fats', 0)
                        )
                        db.session.add(meal)
            except Exception as e:
                logging.error(f"Error generating diet plan: {str(e)}")
            
            # Generate exercise plan
            try:
                exercise_result = generate_exercise_plan(user_info)
                if exercise_result['success']:
                    exercise_data = json.loads(exercise_result['exercise_plan'])
                    
                    new_exercise_plan = ExercisePlan(
                        user_id=current_user.id,
                        title=f"Personalized Exercise Plan for {current_user.first_name}",
                        description=exercise_data.get('description', 'Based on your health profile and lifestyle')
                    )
                    db.session.add(new_exercise_plan)
                    db.session.commit()
                    
                    # Add exercises
                    for exercise_item in exercise_data.get('exercises', []):
                        exercise = Exercise(
                            exercise_plan_id=new_exercise_plan.id,
                            name=exercise_item.get('name', ''),
                            duration=int(exercise_item.get('duration', '0').replace('minutes', '').strip()) if 'minutes' in exercise_item.get('duration', '') else 30,
                            intensity=exercise_item.get('intensity', 'medium'),
                            description=exercise_item.get('description', ''),
                            calories_burned=exercise_item.get('calories_burned', 0)
                        )
                        db.session.add(exercise)
            except Exception as e:
                logging.error(f"Error generating exercise plan: {str(e)}")
            
            db.session.commit()
            flash('Questionnaire completed successfully. Your personalized recommendations are ready!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            logging.error(f"Error processing questionnaire: {str(e)}")
            flash('Error processing questionnaire data', 'danger')
            return redirect(url_for('questionnaire', report_id=report_id))
    
    # Set initial values from user profile
    initial_data = {
        'first_name': current_user.first_name,
        'last_name': current_user.last_name,
        'age': current_user.age,
        'gender': current_user.gender,
        'height': current_user.height,
        'weight': current_user.weight,
        'diabetes_type': current_user.diabetes_type,
        'ethnicity': current_user.ethnicity,
        'diagnosed_date': current_user.diagnosed_date
    }
    
    return render_template(
        'questionnaire.html', 
        questionnaire=questionnaire, 
        report=report, 
        initial_data=initial_data
    )

