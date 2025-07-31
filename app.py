from flask import Flask, request, jsonify
import json
from datetime import datetime, timedelta
import calendar
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

def load_json_file(filename):
    """Load JSON data from file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def get_day_date(day_name):
    """Convert day name to current week's date"""
    today = datetime.now()
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    if day_name not in days:
        return None
    
    target_day = days.index(day_name)
    current_day = today.weekday()
    
    days_ahead = target_day - current_day
    if days_ahead <= 0:
        days_ahead += 7
    
    target_date = today + timedelta(days=days_ahead)
    return target_date.date()

def generate_time_slots():
    """Generate 30-minute time slots from 9 AM to 6 PM, excluding lunch (1-2 PM)"""
    slots = []
    start_hour = 9
    end_hour = 18
    
    for hour in range(start_hour, end_hour):
        # Skip lunch hour (1 PM - 2 PM)
        if hour == 13:
            continue
            
        for minute in [0, 30]:
            time_str = f"{hour:02d}:{minute:02d}"
            slots.append(time_str)
    
    return slots

@app.route('/get_slots')
def get_slots():
    """Get available slots for a specific day"""
    day = request.args.get('day')
    
    if not day:
        return jsonify({"error": "Day parameter is required"}), 400
    
    # Load data
    schedules = load_json_file('schedules.json')
    appointments = load_json_file('appointments.json')
    
    # Check if day exists in schedule
    if day not in schedules:
        return jsonify({"error": f"No schedule found for {day}"}), 404
    
    doctor_info = schedules[day]
    doctor_name = doctor_info['doctor']
    
    # Get target date for the day
    target_date = get_day_date(day)
    if not target_date:
        return jsonify({"error": "Invalid day name"}), 400
    
    # Generate all possible slots
    all_slots = generate_time_slots()
    
    # Filter out booked slots
    booked_slots = set()
    for appointment in appointments:
        appt_date = datetime.fromisoformat(appointment['start_time']).date()
        if appt_date == target_date:
            appt_time = datetime.fromisoformat(appointment['start_time']).time()
            time_str = appt_time.strftime("%H:%M")
            booked_slots.add(time_str)
    
    # Get available slots
    available_slots = [slot for slot in all_slots if slot not in booked_slots]
    
    return jsonify({
        "doctor": doctor_name,
        "available_slots": available_slots,
        "date": target_date.isoformat()
    })

@app.route('/log_booking', methods=['POST'])
def log_booking():
    """Log a new booking"""
    data = request.get_json()
    
    required_fields = ['name', 'doctor', 'day', 'slot']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Log to console
    print(f"New Booking:")
    print(f"  Name: {data['name']}")
    print(f"  Doctor: {data['doctor']}")
    print(f"  Day: {data['day']}")
    print(f"  Slot: {data['slot']}")
    print("-" * 50)
    
    # Save to database, for now => add to appointments.json
    target_date = get_day_date(data['day'])
    if target_date:
        slot_time = datetime.strptime(data['slot'], "%H:%M").time()
        start_datetime = datetime.combine(target_date, slot_time)
        end_datetime = start_datetime + timedelta(minutes=30)
        
        new_appointment = {
            "name": data['name'],
            "start_time": start_datetime.isoformat(),
            "end_time": end_datetime.isoformat()
        }
        
        # Load existing appointments
        appointments = load_json_file('appointments.json')
        appointments.append(new_appointment)
        
        # Save back to file
        with open('appointments.json', 'w') as f:
            json.dump(appointments, f, indent=2)
    
    return jsonify({"message": "Booking logged successfully"})

@app.route('/knowledge')
def get_knowledge():
    """Get knowledge base information"""
    knowledge = load_json_file('knowledge_base.json')
    return jsonify(knowledge)

@app.route('/')
def hello():
    return "Hello, Welcome to ZenfruAI!"

if __name__ == '__main__':
    app.run(debug=True)