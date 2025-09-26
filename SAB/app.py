from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import json

app = Flask(__name__)

# In-memory storage (replace with database in production)
appointments = []

# Available services
services = [
    {
        "id": 1, 
        "name": "General Consultation", 
        "duration": 30, 
        "price": 50,
        "description": "General health checkup and consultation"
    },
    {
        "id": 2, 
        "name": "Dental Checkup", 
        "duration": 45, 
        "price": 75,
        "description": "Complete dental examination and cleaning"
    },
    {
        "id": 3, 
        "name": "Eye Examination", 
        "duration": 30, 
        "price": 60,
        "description": "Comprehensive eye health assessment"
    },
    {
        "id": 4, 
        "name": "Physical Therapy", 
        "duration": 60, 
        "price": 100,
        "description": "Therapeutic exercise and rehabilitation"
    },
    {
        "id": 5, 
        "name": "Skin Treatment", 
        "duration": 45, 
        "price": 85,
        "description": "Dermatology consultation and treatment"
    }
]

@app.route('/')
def index():
    """Render the main booking page"""
    return render_template('index.html')

@app.route('/api/services', methods=['GET'])
def get_services():
    """Get all available services"""
    return jsonify(services)

@app.route('/api/available-slots', methods=['POST'])
def get_available_slots():
    """Get available time slots for a specific date and service"""
    try:
        data = request.json
        date = data.get('date')
        service_id = data.get('service_id')
        
        if not date or not service_id:
            return jsonify({"error": "Date and service_id are required"}), 400
        
        # Validate date format
        try:
            selected_date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Don't allow booking for past dates
        if selected_date.date() < datetime.now().date():
            return jsonify([])
        
        # Generate time slots (9 AM to 5 PM, every 30 minutes)
        slots = []
        base_date = datetime.strptime(date, '%Y-%m-%d')
        
        for hour in range(9, 17):  # 9 AM to 5 PM
            for minute in [0, 30]:
                slot_time = base_date.replace(hour=hour, minute=minute)
                slot_str = slot_time.strftime('%H:%M')
                
                # Check if slot is already booked
                is_booked = any(
                    apt['date'] == date and apt['time'] == slot_str 
                    for apt in appointments
                )
                
                # If it's today, only show future time slots
                if selected_date.date() == datetime.now().date():
                    current_time = datetime.now().time()
                    slot_time_obj = slot_time.time()
                    if slot_time_obj <= current_time:
                        continue
                
                if not is_booked:
                    slots.append(slot_str)
        
        return jsonify(slots)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/book', methods=['POST'])
def book_appointment():
    """Book a new appointment"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['name', 'email', 'phone', 'service_id', 'date', 'time']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "success": False, 
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Validate email format (basic validation)
        if '@' not in data['email']:
            return jsonify({
                "success": False, 
                "message": "Invalid email format"
            }), 400
        
        # Validate service exists
        service = next((s for s in services if s['id'] == data['service_id']), None)
        if not service:
            return jsonify({
                "success": False, 
                "message": "Invalid service selected"
            }), 400
        
        # Check if slot is still available
        is_booked = any(
            apt['date'] == data['date'] and apt['time'] == data['time'] 
            for apt in appointments
        )
        
        if is_booked:
            return jsonify({
                "success": False, 
                "message": "This time slot is no longer available. Please select another time."
            }), 409
        
        # Validate date is not in the past
        try:
            appointment_date = datetime.strptime(data['date'], '%Y-%m-%d')
            if appointment_date.date() < datetime.now().date():
                return jsonify({
                    "success": False, 
                    "message": "Cannot book appointments in the past"
                }), 400
        except ValueError:
            return jsonify({
                "success": False, 
                "message": "Invalid date format"
            }), 400
        
        # Create appointment
        appointment = {
            "id": len(appointments) + 1,
            "name": data['name'].strip(),
            "email": data['email'].strip().lower(),
            "phone": data['phone'].strip(),
            "service_id": data['service_id'],
            "service_name": service['name'],
            "date": data['date'],
            "time": data['time'],
            "notes": data.get('notes', '').strip(),
            "status": "confirmed",
            "created_at": datetime.now().isoformat()
        }
        
        appointments.append(appointment)
        
        return jsonify({
            "success": True, 
            "message": "Appointment booked successfully!",
            "appointment_id": appointment['id'],
            "appointment": appointment
        }), 201
    
    except Exception as e:
        return jsonify({
            "success": False, 
            "message": f"An error occurred: {str(e)}"
        }), 500

@app.route('/api/appointments', methods=['GET'])
def get_appointments():
    """Get all appointments (for admin view)"""
    return jsonify({
        "total": len(appointments),
        "appointments": appointments
    })

@app.route('/api/appointments/<int:appointment_id>', methods=['GET'])
def get_appointment(appointment_id):
    """Get a specific appointment by ID"""
    appointment = next((apt for apt in appointments if apt['id'] == appointment_id), None)
    
    if appointment:
        return jsonify(appointment)
    else:
        return jsonify({"error": "Appointment not found"}), 404

@app.route('/api/appointments/<int:appointment_id>', methods=['DELETE'])
def cancel_appointment(appointment_id):
    """Cancel an appointment"""
    global appointments
    
    appointment = next((apt for apt in appointments if apt['id'] == appointment_id), None)
    
    if appointment:
        appointments = [apt for apt in appointments if apt['id'] != appointment_id]
        return jsonify({
            "success": True,
            "message": "Appointment cancelled successfully"
        })
    else:
        return jsonify({
            "success": False,
            "message": "Appointment not found"
        }), 404

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Smart Appointment Booking System")
    print("=" * 50)
    print("📍 Server running at: http://localhost:5000")
    print("📋 Available endpoints:")
    print("   - GET  /                          (Main booking page)")
    print("   - GET  /api/services              (Get all services)")
    print("   - POST /api/available-slots       (Get available time slots)")
    print("   - POST /api/book                  (Book an appointment)")
    print("   - GET  /api/appointments          (Get all appointments)")
    print("   - GET  /api/appointments/<id>     (Get specific appointment)")
    print("   - DELETE /api/appointments/<id>   (Cancel appointment)")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)