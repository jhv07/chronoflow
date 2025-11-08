from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
from bson import ObjectId
from datetime import datetime
import hashlib
import threading
import time
from werkzeug.security import generate_password_hash, check_password_hash
# MongoDB Connection
app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/chronoflow'
CORS(app)

mongo = PyMongo(app)

# Background thread for checking events
event_check_thread = None
stop_event_check = threading.Event()

class JSONEncoder:
    """Custom JSON encoder for ObjectId"""
    @staticmethod
    def default(obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        raise TypeError(f'Object of type {type(obj)} is not JSON serializable')

# ===== Authentication Routes =====
@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email or not password:
            return jsonify({'message': 'All fields are required'}), 400
        
        # Check if user already exists
        existing_user = mongo.db.users.find_one({'email': email})
        if existing_user:
            return jsonify({'message': 'User already exists'}), 409
        
        # Create new user
        hashed_password = generate_password_hash(password)
        user = {
            'username': username,
            'email': email,
            'password': hashed_password,
            'created_at': datetime.now()
        }
        
        result = mongo.db.users.insert_one(user)
        user['_id'] = str(result.inserted_id)
        user.pop('password', None)  # Remove password from response
        
        return jsonify({
            'message': 'User created successfully',
            'user': user
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'message': 'Email and password are required'}), 400
        
        user = mongo.db.users.find_one({'email': email})
        if not user:
            return jsonify({'message': 'Invalid credentials'}), 401
        
        if not check_password_hash(user['password'], password):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        user['_id'] = str(user['_id'])
        user.pop('password', None)  # Remove password from response
        
        return jsonify({
            'message': 'Login successful',
            'user': user
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ===== Event Routes =====
@app.route('/add_event', methods=['POST'])
def add_event():
    try:
        data = request.json
        email = data.get('email')
        title = data.get('title')
        date = data.get('date')
        time = data.get('time')
        
        if not email or not title or not date or not time:
            return jsonify({'message': 'Missing required fields'}), 400
        
        event = {
            'email': email,
            'title': title,
            'description': data.get('description', ''),
            'date': date,
            'time': time,
            'category': data.get('category', 'personal'),
            'reminder': data.get('reminder', 'both'),
            'photo': data.get('photo'),
            'soundType': data.get('soundType', 'chime'),
            'triggered': data.get('triggered', False),
            'bgColor': data.get('bgColor', '#6c5ce7'),
            'created_at': datetime.now()
        }
        
        result = mongo.db.events.insert_one(event)
        event['_id'] = str(result.inserted_id)
        
        return jsonify({
            'message': 'Event added successfully',
            'event': event
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/get_events', methods=['GET'])
def get_events():
    try:
        email = request.args.get('email')
        
        if not email:
            return jsonify({'message': 'Email parameter is required'}), 400
        
        events = list(mongo.db.events.find({'email': email}))
        
        # Convert ObjectId to string
        for event in events:
            event['_id'] = str(event['_id'])
        
        return jsonify({
            'message': 'Events retrieved successfully',
            'events': events
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/delete_event/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    try:
        if not ObjectId.is_valid(event_id):
            return jsonify({'message': 'Invalid event ID'}), 400
        
        result = mongo.db.events.delete_one({'_id': ObjectId(event_id)})
        
        if result.deleted_count == 0:
            return jsonify({'message': 'Event not found'}), 404
        
        return jsonify({'message': 'Event deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/update_event/<event_id>', methods=['PUT'])
def update_event(event_id):
    try:
        if not ObjectId.is_valid(event_id):
            return jsonify({'message': 'Invalid event ID'}), 400
        
        data = request.json
        update_data = {k: v for k, v in data.items() if k != '_id' and k != 'email'}
        update_data['updated_at'] = datetime.now()
        
        result = mongo.db.events.update_one(
            {'_id': ObjectId(event_id)},
            {'$set': update_data}
        )
        
        if result.modified_count == 0:
            return jsonify({'message': 'Event not found or no changes made'}), 404
        
        return jsonify({'message': 'Event updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ===== Background Event Checker =====
def check_events():
    """Background thread to check for due events"""
    while not stop_event_check.is_set():
        try:
            current_time = datetime.now()
            current_date_str = current_time.strftime('%Y-%m-%d')
            current_time_str = current_time.strftime('%H:%M:%S')
            
            # Find events that are due
            due_events = mongo.db.events.find({
                'triggered': False,
                'date': current_date_str,
                'time': current_time_str
            })
            
            for event in due_events:
                # You could send web push notifications here
                # For now, we'll just mark as triggered
                print(f"Event triggered: {event['title']} for {event['email']}")
                
                # Optionally mark as triggered
                # mongo.db.events.update_one(
                #     {'_id': event['_id']},
                #     {'$set': {'triggered': True}}
                # )
            
        except Exception as e:
            print(f"Error checking events: {str(e)}")
        
        # Sleep for 60 seconds before checking again
        stop_event_check.wait(60)

# ===== Health Check =====
@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Check MongoDB connection
        mongo.db.command('ping')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ===== Initialize Background Thread =====
def start_background_checker():
    global event_check_thread
    if event_check_thread is None or not event_check_thread.is_alive():
        stop_event_check.clear()
        event_check_thread = threading.Thread(target=check_events, daemon=True)
        event_check_thread.start()
        print("Background event checker started")

# ===== Startup =====
if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 ChronoFlow Server Starting...")
    print("="*50)
    print(f"Database: {app.config['MONGO_URI']}")
    print("="*50 + "\n")
    
    # Start background thread immediately
    start_background_checker()
    
    app.run(debug=True, host='0.0.0.0', port=5000)

