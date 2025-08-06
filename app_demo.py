import os
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import uuid
from textblob import TextBlob
from decimal import Decimal

# Load environment variables
load_dotenv()

# ---------------------------------------
# Flask App Initialization
# ---------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'capture_moments_secret_key_2024')

# Mock database for demo (in production, this would be DynamoDB)
mock_db = {
    'users': {},
    'photographers': {},
    'bookings': {},
    'feedback': {}
}

# Initialize with demo data
def init_demo_data():
    # Demo users
    demo_users = [
        {
            'user_id': str(uuid.uuid4()),
            'email': 'client@demo.com',
            'username': 'Demo Client',
            'password': generate_password_hash('demo123'),
            'role': 'client',
            'created_at': datetime.now().isoformat(),
            'is_active': True
        },
        {
            'user_id': str(uuid.uuid4()),
            'email': 'photographer@demo.com',
            'username': 'Demo Photographer',
            'password': generate_password_hash('demo123'),
            'role': 'photographer',
            'created_at': datetime.now().isoformat(),
            'is_active': True
        },
        {
            'user_id': str(uuid.uuid4()),
            'email': 'admin@demo.com',
            'username': 'Demo Admin',
            'password': generate_password_hash('demo123'),
            'role': 'admin',
            'created_at': datetime.now().isoformat(),
            'is_active': True
        }
    ]
    
    for user in demo_users:
        mock_db['users'][user['email']] = user
    
    # Demo photographers
    photographer_user = next(u for u in demo_users if u['role'] == 'photographer')
    demo_photographers = [
        {
            'photographer_id': photographer_user['user_id'],
            'name': 'Rajesh Kumar',
            'email': 'rajesh@capturemoments.com',
            'specialization': 'Wedding Photography',
            'location': 'Hyderabad, India',
            'bio': 'Professional wedding photographer with 8+ years experience in capturing beautiful moments',
            'years_experience': 8,
            'price_range': 'Premium',
            'average_rating': 4.8,
            'is_active': True,
            'created_at': datetime.now().isoformat()
        },
        {
            'photographer_id': str(uuid.uuid4()),
            'name': 'Priya Sharma',
            'email': 'priya@capturemoments.com',
            'specialization': 'Portrait Photography',
            'location': 'Mumbai, India',
            'bio': 'Creative portrait photographer specializing in family and individual sessions',
            'years_experience': 5,
            'price_range': 'Medium',
            'average_rating': 4.6,
            'is_active': True,
            'created_at': datetime.now().isoformat()
        },
        {
            'photographer_id': str(uuid.uuid4()),
            'name': 'Amit Patel',
            'email': 'amit@capturemoments.com',
            'specialization': 'Event Photography',
            'location': 'Delhi, India',
            'bio': 'Corporate and social event photographer with modern artistic style',
            'years_experience': 6,
            'price_range': 'Medium',
            'average_rating': 4.7,
            'is_active': True,
            'created_at': datetime.now().isoformat()
        }
    ]
    
    for photographer in demo_photographers:
        mock_db['photographers'][photographer['photographer_id']] = photographer

# Initialize demo data
init_demo_data()

# ---------------------------------------
# Utility Functions
# ---------------------------------------
def analyze_sentiment(text):
    """Analyze sentiment of text using TextBlob"""
    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        if polarity > 0.1:
            return 'positive', polarity
        elif polarity < -0.1:
            return 'negative', polarity
        else:
            return 'neutral', polarity
    except:
        return 'neutral', 0.0

def login_required(f):
    """Decorator for routes that require login"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def admin_required(f):
    """Decorator for admin-only routes"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'admin':
            flash('Admin access required')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# ---------------------------------------
# Authentication Routes
# ---------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'client')
        
        if not all([username, email, password]):
            flash('All fields are required')
            return render_template('register.html')
        
        # Check if user already exists
        if email in mock_db['users']:
            flash('User already exists')
            return render_template('register.html')
        
        # Create new user
        user_id = str(uuid.uuid4())
        hashed_password = generate_password_hash(password)
        
        user_data = {
            'user_id': user_id,
            'email': email,
            'username': username,
            'password': hashed_password,
            'role': role,
            'created_at': datetime.now().isoformat(),
            'is_active': True
        }
        
        mock_db['users'][email] = user_data
        flash('Registration successful')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        email = data.get('email')
        password = data.get('password')
        
        if not all([email, password]):
            flash('Email and password required')
            return render_template('login.html')
        
        user = mock_db['users'].get(email)
        if not user:
            flash('Invalid credentials')
            return render_template('login.html')
        
        if not user.get('is_active', True):
            flash('Account deactivated')
            return render_template('login.html')
        
        if check_password_hash(user['password'], password):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['email'] = user['email']
            session['user_role'] = user.get('role', 'client')
            
            flash(f'Welcome back, {user["username"]}!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully')
    return redirect(url_for('index'))

# ---------------------------------------
# Dashboard Routes
# ---------------------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    user_role = session.get('user_role', 'client')
    if user_role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif user_role == 'photographer':
        return redirect(url_for('photographer_dashboard'))
    else:
        return redirect(url_for('client_dashboard'))

@app.route('/client/dashboard')
@login_required
def client_dashboard():
    photographers = list(mock_db['photographers'].values())
    user_bookings = [b for b in mock_db['bookings'].values() if b.get('user_id') == session['user_id']]
    return render_template('client_dashboard.html', photographers=photographers, user_bookings=user_bookings)

@app.route('/photographer/dashboard')
@login_required
def photographer_dashboard():
    photographer_profile = mock_db['photographers'].get(session['user_id'], {})
    pending_bookings = [b for b in mock_db['bookings'].values() 
                       if b.get('photographer_id') == session['user_id'] and b.get('booking_status') == 'pending']
    confirmed_bookings = [b for b in mock_db['bookings'].values() 
                         if b.get('photographer_id') == session['user_id'] and b.get('booking_status') == 'confirmed']
    
    return render_template('photographer_dashboard.html',
                         photographer_profile=photographer_profile,
                         pending_bookings=pending_bookings,
                         confirmed_bookings=confirmed_bookings)

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    bookings = list(mock_db['bookings'].values())
    feedback_items = list(mock_db['feedback'].values())
    
    booking_stats = {'pending': 0, 'confirmed': 0, 'completed': 0, 'cancelled': 0}
    for booking in bookings:
        status = booking.get('booking_status', 'pending')
        if status in booking_stats:
            booking_stats[status] += 1
    
    sentiment_stats = {'positive': 0, 'negative': 0, 'neutral': 0}
    for feedback in feedback_items:
        sentiment = feedback.get('sentiment', 'neutral')
        if sentiment in sentiment_stats:
            sentiment_stats[sentiment] += 1
    
    negative_feedback = [f for f in feedback_items if f.get('sentiment') == 'negative']
    
    return render_template('admin_dashboard.html',
                         bookings=bookings,
                         booking_stats=booking_stats,
                         sentiment_stats=sentiment_stats,
                         negative_feedback=negative_feedback,
                         total_bookings=len(bookings))

# ---------------------------------------
# Photographer Routes
# ---------------------------------------
@app.route('/photographers')
@login_required
def photographers():
    photographers_list = list(mock_db['photographers'].values())
    return render_template('photographers.html', photographers=photographers_list)

# ---------------------------------------
# Advanced Features - AI Recommendations
# ---------------------------------------
@app.route('/api/recommendations')
def get_recommendations():
    """AI-powered photographer recommendations"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    event_type = request.args.get('event_type', 'wedding')
    location = request.args.get('location', 'hyderabad')

    # Simple recommendation algorithm
    photographers = list(mock_db['photographers'].values())
    recommendations = []

    for photographer in photographers:
        score = 0
        # Match specialization
        if event_type.lower() in photographer.get('specialization', '').lower():
            score += 3
        # Match location
        if location.lower() in photographer.get('location', '').lower():
            score += 2
        # Add rating bonus
        score += photographer.get('average_rating', 4.0) / 5.0

        recommendations.append({
            'photographer': photographer,
            'score': score,
            'match_reasons': [
                f"Specializes in {photographer.get('specialization')}",
                f"Located in {photographer.get('location')}",
                f"Rated {photographer.get('average_rating')}/5.0"
            ]
        })

    # Sort by score
    recommendations.sort(key=lambda x: x['score'], reverse=True)

    return jsonify({
        'recommendations': recommendations[:5],
        'total_found': len(recommendations),
        'search_criteria': {'event_type': event_type, 'location': location}
    })

@app.route('/api/pricing')
def get_dynamic_pricing():
    """Dynamic pricing calculation"""
    event_type = request.args.get('event_type', 'wedding')
    location = request.args.get('location', 'hyderabad')
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    duration = int(request.args.get('duration', 2))

    # Base prices
    base_prices = {
        'wedding': 1500,
        'portrait': 300,
        'event': 800,
        'commercial': 1200
    }

    base_price = base_prices.get(event_type.lower(), 500)

    # Location multiplier
    location_multipliers = {
        'mumbai': 1.5,
        'delhi': 1.4,
        'bangalore': 1.3,
        'hyderabad': 1.2,
        'chennai': 1.2
    }

    location_multiplier = 1.0
    for city, multiplier in location_multipliers.items():
        if city in location.lower():
            location_multiplier = multiplier
            break

    # Date multiplier (weekend premium)
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        date_multiplier = 1.2 if date_obj.weekday() >= 5 else 1.0
    except:
        date_multiplier = 1.0

    # Duration multiplier
    duration_multiplier = max(1.0, duration / 2.0)

    final_price = base_price * location_multiplier * date_multiplier * duration_multiplier

    return jsonify({
        'base_price': base_price,
        'final_price': round(final_price, 2),
        'factors': {
            'location_multiplier': location_multiplier,
            'date_multiplier': date_multiplier,
            'duration_multiplier': duration_multiplier,
            'weekend_premium': date_multiplier > 1.0
        },
        'breakdown': {
            'event_type': event_type,
            'location': location,
            'date': date,
            'duration_hours': duration
        }
    })

@app.route('/api/sentiment-analysis')
def analyze_feedback_sentiment():
    """Sentiment analysis of feedback"""
    feedback_items = list(mock_db['feedback'].values())

    sentiment_stats = {'positive': 0, 'negative': 0, 'neutral': 0}
    analyzed_feedback = []

    for feedback in feedback_items:
        text = feedback.get('message', '')
        sentiment, score = analyze_sentiment(text)

        sentiment_stats[sentiment] += 1
        analyzed_feedback.append({
            'feedback_id': feedback.get('feedback_id'),
            'sentiment': sentiment,
            'score': score,
            'text_preview': text[:100] + '...' if len(text) > 100 else text
        })

    return jsonify({
        'sentiment_stats': sentiment_stats,
        'analyzed_feedback': analyzed_feedback,
        'total_feedback': len(feedback_items)
    })

# ---------------------------------------
# Booking System with Advanced Features
# ---------------------------------------
@app.route('/api/book-photographer', methods=['POST'])
def book_photographer_api():
    """Enhanced booking with conflict detection"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    data = request.get_json()
    photographer_id = data.get('photographer_id')
    event_date = data.get('event_date')
    event_time = data.get('event_time')
    duration = int(data.get('duration', 2))

    # Check for conflicts
    conflicts = []
    for booking in mock_db['bookings'].values():
        if (booking.get('photographer_id') == photographer_id and
            booking.get('event_date') == event_date and
            booking.get('booking_status') in ['confirmed', 'pending']):
            conflicts.append(booking)

    if conflicts:
        return jsonify({
            'success': False,
            'error': 'Time slot conflict detected',
            'conflicts': conflicts
        }), 409

    # Create booking
    booking_id = str(uuid.uuid4())
    booking = {
        'booking_id': booking_id,
        'user_id': session['user_id'],
        'photographer_id': photographer_id,
        'event_date': event_date,
        'event_time': event_time,
        'duration': duration,
        'booking_status': 'pending',
        'created_at': datetime.now().isoformat(),
        'client_name': session['username']
    }

    mock_db['bookings'][booking_id] = booking

    return jsonify({
        'success': True,
        'booking_id': booking_id,
        'message': 'Booking request submitted successfully'
    })

# ---------------------------------------
# API Routes for Demo
# ---------------------------------------
@app.route('/api/demo-status')
def demo_status():
    return jsonify({
        'status': 'running',
        'users': len(mock_db['users']),
        'photographers': len(mock_db['photographers']),
        'bookings': len(mock_db['bookings']),
        'features': [
            'User Authentication',
            'Role-based Access Control',
            'Photographer Profiles',
            'AI Recommendations',
            'Dynamic Pricing',
            'Sentiment Analysis',
            'Booking System',
            'Responsive Design'
        ],
        'advanced_features': [
            'AI-Powered Recommendations',
            'Dynamic Pricing Engine',
            'Sentiment Analysis',
            'Conflict Detection',
            'Real-time Analytics'
        ]
    })

# ---------------------------------------
# Error Handlers
# ---------------------------------------
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error='Internal server error'), 500

if __name__ == '__main__':
    print("🚀 Starting Capture Moments Demo Server...")
    print("=" * 60)
    print("📝 Demo Accounts Available:")
    print("   Client: client@demo.com / demo123")
    print("   Photographer: photographer@demo.com / demo123") 
    print("   Admin: admin@demo.com / demo123")
    print("=" * 60)
    print("🌐 Server will be available at: http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
