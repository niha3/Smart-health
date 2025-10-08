from flask import Flask, render_template, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

# -------------------------------
# In-memory storage (replace with DB in production)
# -------------------------------
appointments = []

services = [
    {"id": 1, "name": "General Consultation", "duration": 30, "price": 50, "description": "General health checkup and consultation"},
    {"id": 2, "name": "Dental Checkup", "duration": 45, "price": 75, "description": "Complete dental examination and cleaning"},
    {"id": 3, "name": "Eye Examination", "duration": 30, "price": 60, "description": "Comprehensive eye health assessment"},
    {"id": 4, "name": "Physical Therapy", "duration": 60, "price": 100, "description": "Therapeutic exercise and rehabilitation"},
    {"id": 5, "name": "Skin Treatment", "duration": 45, "price": 85, "description": "Dermatology consultation and treatment"},
]

# -------------------------------
# Routes
# -------------------------------
@app.route('/')
def index():
    """Render main booking page"""
    return render_template('index.html')


@app.route('/api/services', methods=['GET'])
def get_services():
    """Return all services"""
    return jsonify(services)


@app.route('/api/available-slots', methods=['POST'])
def get_available_slots():
    """Return available time slots for selected service & date"""
    try:
        data = request.json
        date = data.get('date')
        service_id = data.get('service_id')

        if not date or not service_id:
            return jsonify({"error": "Date and service_id are required"}), 400

        try:
            selected_date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

        if selected_date.date() < datetime.now().date():
            return jsonify([])  # No slots in past

        # Generate slots: 9AM to 5PM, 30 min intervals
        slots = []
        for hour in range(9, 17):
            for minute in [0, 30]:
                slot_time = selected_date.replace(hour=hour, minute=minute)
                slot_str = slot_time.strftime('%H:%M')

                # Skip if already booked
                is_booked = any(
                    apt['date'] == date and apt['time'] == slot_str for apt in appointments
                )

                # If today, skip past times
                if selected_date.date() == datetime.now().date():
                    if slot_time.time() <= datetime.now().time():
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
        required_fields = ['name', 'email', 'phone', 'service_id', 'date', 'time']
        missing = [f for f in required_fields if f not in data]

        if missing:
            return jsonify({"success": False, "message": f"Missing fields: {', '.join(missing)}"}), 400

        if '@' not in data['email']:
            return jsonify({"success": False, "message": "Invalid email"}), 400

        service = next((s for s in services if s['id'] == data['service_id']), None)
        if not service:
            return jsonify({"success": False, "message": "Invalid service"}), 400

        # Check if slot is free
        if any(apt['date'] == data['date'] and apt['time'] == data['time'] for apt in appointments):
            return jsonify({"success": False, "message": "Time slot unavailable"}), 409

        # Check date not in past
        appt_date = datetime.strptime(data['date'], '%Y-%m-%d')
        if appt_date.date() < datetime.now().date():
            return jsonify({"success": False, "message": "Cannot book past dates"}), 400

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

        return jsonify({"success": True, "appointment_id": appointment['id'], "appointment": appointment}), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/appointments', methods=['GET'])
def get_appointments():
    """Return all appointments"""
    return jsonify({"total": len(appointments), "appointments": appointments})


@app.route('/api/appointments/<int:appointment_id>', methods=['GET'])
def get_appointment(appointment_id):
    """Get a single appointment by ID"""
    appointment = next((apt for apt in appointments if apt['id'] == appointment_id), None)
    if appointment:
        return jsonify(appointment)
    return jsonify({"error": "Appointment not found"}), 404


@app.route('/api/appointments/<int:appointment_id>', methods=['DELETE'])
def cancel_appointment(appointment_id):
    """Cancel an appointment"""
    global appointments
    appointment = next((apt for apt in appointments if apt['id'] == appointment_id), None)
    if appointment:
        appointments = [apt for apt in appointments if apt['id'] != appointment_id]
        return jsonify({"success": True, "message": "Appointment cancelled"})
    return jsonify({"success": False, "message": "Appointment not found"}), 404


# Error handlers

@app.errorhandler(500)
def error_message(error):
    return jsonify({"error": "Internal server error. Please Try Again"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404



# Run server
if __name__ == '__main__':
    print("="*50)
    print("🚀 Smart Appointment Booking System")
    print("="*50)
    print("📍 Server running at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
