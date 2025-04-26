from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    diabetes_type = db.Column(db.String(20))
    ethnicity = db.Column(db.String(64))
    diagnosed_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    blood_sugar_entries = db.relationship('BloodSugarEntry', backref='user', lazy=True, cascade="all, delete-orphan")
    medical_records = db.relationship('MedicalRecord', backref='user', lazy=True, cascade="all, delete-orphan")
    medications = db.relationship('Medication', backref='user', lazy=True, cascade="all, delete-orphan")
    diet_plans = db.relationship('DietPlan', backref='user', lazy=True, cascade="all, delete-orphan")
    exercise_plans = db.relationship('ExercisePlan', backref='user', lazy=True, cascade="all, delete-orphan")
    report_analyses = db.relationship('ReportAnalysis', backref='user', lazy=True, cascade="all, delete-orphan")
    questionnaires = db.relationship('Questionnaire', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_bmi(self):
        if self.height and self.weight:
            height_m = self.height / 100
            return round(self.weight / (height_m * height_m), 1)
        return None

    def __repr__(self):
        return f'<User {self.username}>'

class BloodSugarEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    value = db.Column(db.Float, nullable=False)
    measured_at = db.Column(db.DateTime, default=datetime.utcnow)
    meal_status = db.Column(db.String(20))
    notes = db.Column(db.Text)

    def __repr__(self):
        return f'<BloodSugar {self.value} mg/dL at {self.measured_at}>'

class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    record_type = db.Column(db.String(64), nullable=False)
    record_date = db.Column(db.Date, nullable=False)
    doctor = db.Column(db.String(128))
    clinic = db.Column(db.String(128))
    file_path = db.Column(db.String(256))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MedicalRecord {self.record_type} from {self.record_date}>'

class Medication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    dosage = db.Column(db.String(64))
    frequency = db.Column(db.String(64))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)

    def __repr__(self):
        return f'<Medication {self.name} {self.dosage}>'

class DietPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    calories = db.Column(db.Integer)
    carbs = db.Column(db.Integer)
    proteins = db.Column(db.Integer)
    fats = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    meals = db.relationship('Meal', backref='diet_plan', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<DietPlan {self.title}>'

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    diet_plan_id = db.Column(db.Integer, db.ForeignKey('diet_plan.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    time = db.Column(db.String(64))
    description = db.Column(db.Text)
    calories = db.Column(db.Integer)
    carbs = db.Column(db.Integer)
    proteins = db.Column(db.Integer)
    fats = db.Column(db.Integer)

    def __repr__(self):
        return f'<Meal {self.name} for {self.time}>'

class ExercisePlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    exercises = db.relationship('Exercise', backref='exercise_plan', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<ExercisePlan {self.title}>'

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exercise_plan_id = db.Column(db.Integer, db.ForeignKey('exercise_plan.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    duration = db.Column(db.Integer)
    intensity = db.Column(db.String(64))
    description = db.Column(db.Text)
    calories_burned = db.Column(db.Integer)

    def __repr__(self):
        return f'<Exercise {self.name} ({self.duration} min)>'

class ReportAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_path = db.Column(db.String(256))
    analysis_result = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    questionnaire = db.relationship('Questionnaire', backref='report', lazy=True, uselist=False)

    def __repr__(self):
        return f'<ReportAnalysis for user {self.user_id} at {self.created_at}>'

class Questionnaire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey('report_analysis.id'), nullable=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    activity_level = db.Column(db.String(64))
    occupation_type = db.Column(db.String(64))
    dietary_restrictions = db.Column(db.String(256))
    medical_conditions = db.Column(db.String(256))
    medications_list = db.Column(db.String(256))
    other_medications = db.Column(db.Text)
    allergies = db.Column(db.Text)
    additional_info = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Questionnaire for user {self.user_id}>'
