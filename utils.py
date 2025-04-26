import os
import datetime
import io
import logging
import uuid
import PyPDF2
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename):
    """Check if the file has an allowed extension"""
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, subfolder=""):
    """
    Save the uploaded file to the upload folder
    
    Args:
        file: The file to save
        subfolder: Optional subfolder within the upload folder
        
    Returns:
        str: The path to the saved file
    """
    if not file:
        return None
        
    folder = current_app.config['UPLOAD_FOLDER']
    if subfolder:
        folder = os.path.join(folder, subfolder)
        os.makedirs(folder, exist_ok=True)
    
    filename = secure_filename(file.filename)
    # Add timestamp to ensure uniqueness
    unique_filename = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
    file_path = os.path.join(folder, unique_filename)
    file.save(file_path)
    
    return file_path

def extract_text_from_pdf(file_path):
    """
    Extract text from a PDF file
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        str: Extracted text
    """
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return ""
        
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(reader.pages)):
                text += reader.pages[page_num].extract_text()
            return text
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {str(e)}")
        return ""

def format_date(date):
    """Format date for display"""
    if isinstance(date, str):
        try:
            date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return date
    if isinstance(date, datetime.date):
        return date.strftime('%b %d, %Y')
    return date

def calculate_statistics(blood_sugar_entries):
    """
    Calculate statistics from blood sugar entries
    
    Args:
        blood_sugar_entries: List of BloodSugarEntry objects
        
    Returns:
        dict: Statistics including average, min, max, etc.
    """
    if not blood_sugar_entries:
        return {
            "average": 0,
            "min": 0,
            "max": 0,
            "readings_count": 0,
            "in_range_count": 0,
            "in_range_percentage": 0,
            "high_count": 0,
            "low_count": 0
        }
    
    values = [entry.value for entry in blood_sugar_entries]
    
    # Define ranges (mg/dL)
    low_threshold = 70
    high_threshold = 180
    
    # Calculate statistics
    avg = sum(values) / len(values)
    min_val = min(values)
    max_val = max(values)
    readings_count = len(values)
    
    # Count readings in different ranges
    in_range_count = sum(1 for v in values if low_threshold <= v <= high_threshold)
    high_count = sum(1 for v in values if v > high_threshold)
    low_count = sum(1 for v in values if v < low_threshold)
    
    # Calculate percentages
    in_range_percentage = (in_range_count / readings_count) * 100 if readings_count > 0 else 0
    
    return {
        "average": round(avg, 1),
        "min": min_val,
        "max": max_val,
        "readings_count": readings_count,
        "in_range_count": in_range_count,
        "in_range_percentage": round(in_range_percentage, 1),
        "high_count": high_count,
        "low_count": low_count
    }

def get_progress_metrics(user, days=30):
    """
    Get progress metrics for a user over a specific period
    
    Args:
        user: User object
        days: Number of days to look back
        
    Returns:
        dict: Progress metrics
    """
    from models import BloodSugarEntry
    
    # Calculate date range
    end_date = datetime.datetime.utcnow()
    start_date = end_date - datetime.timedelta(days=days)
    
    # Query blood sugar entries in date range
    entries = BloodSugarEntry.query.filter(
        BloodSugarEntry.user_id == user.id,
        BloodSugarEntry.measured_at >= start_date,
        BloodSugarEntry.measured_at <= end_date
    ).order_by(BloodSugarEntry.measured_at).all()
    
    # Calculate statistics
    stats = calculate_statistics(entries)
    
    # Prepare data for charts
    chart_data = []
    for entry in entries:
        chart_data.append({
            "date": entry.measured_at.strftime('%Y-%m-%d'),
            "time": entry.measured_at.strftime('%H:%M'),
            "value": entry.value,
            "meal_status": entry.meal_status or "unknown"
        })
    
    return {
        "statistics": stats,
        "chart_data": chart_data
    }

def group_entries_by_date(entries):
    """Group blood sugar entries by date"""
    result = {}
    for entry in entries:
        date_str = entry.measured_at.strftime('%Y-%m-%d')
        if date_str not in result:
            result[date_str] = []
        result[date_str].append(entry)
    return result
