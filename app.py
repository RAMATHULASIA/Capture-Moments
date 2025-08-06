import os
import boto3
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import uuid
from textblob import TextBlob
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from decimal import Decimal

# Load environment variables
load_dotenv()

# ---------------------------------------
# Flask App Initialization
# ---------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'capture_moments_secret_key_2024')

# Import and register advanced feature blueprints
from advanced_features import advanced_bp
from ai_features import ai_bp
from chat_system import chat_bp, init_socketio

app.register_blueprint(advanced_bp, url_prefix='/advanced')
app.register_blueprint(ai_bp, url_prefix='/ai')
app.register_blueprint(chat_bp, url_prefix='/chat')

# Initialize SocketIO for real-time chat
socketio = init_socketio(app)

# ---------------------------------------
# App Configuration
# ---------------------------------------
AWS_REGION_NAME = os.environ.get('AWS_REGION_NAME', 'ap-south-1')

# Email Configuration
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD')
ENABLE_EMAIL = os.environ.get('ENABLE_EMAIL', 'False').lower() == 'true'

# Table Names from .env
USERS_TABLE_NAME = os.environ.get('USERS_TABLE_NAME', 'CaptureMomentsUsers')
PHOTOGRAPHERS_TABLE_NAME = os.environ.get('PHOTOGRAPHERS_TABLE_NAME', 'CaptureMomentsPhotographers')
BOOKINGS_TABLE_NAME = os.environ.get('BOOKINGS_TABLE_NAME', 'CaptureMomentsBookings')
FEEDBACK_TABLE_NAME = os.environ.get('FEEDBACK_TABLE_NAME', 'CaptureMomentsFeedback')

# SNS Configuration
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
ENABLE_SNS = os.environ.get('ENABLE_SNS', 'False').lower() == 'true'

# ---------------------------------------
# AWS Resources
# ---------------------------------------
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION_NAME)
sns = boto3.client('sns', region_name=AWS_REGION_NAME)

# DynamoDB Tables
users_table = dynamodb.Table(USERS_TABLE_NAME)
photographers_table = dynamodb.Table(PHOTOGRAPHERS_TABLE_NAME)
bookings_table = dynamodb.Table(BOOKINGS_TABLE_NAME)
feedback_table = dynamodb.Table(FEEDBACK_TABLE_NAME)

# ---------------------------------------
# Utility Functions
# ---------------------------------------
def analyze_sentiment(text):
    """Analyze sentiment of text using TextBlob"""
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        return 'positive', polarity
    elif polarity < -0.1:
        return 'negative', polarity
    else:
        return 'neutral', polarity

def send_sns_alert(message, subject):
    """Send SNS alert for negative feedback or urgent notifications"""
    if ENABLE_SNS and SNS_TOPIC_ARN:
        try:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=message,
                Subject=subject
            )
            return True
        except Exception as e:
            print(f"SNS Error: {e}")
            return False
    return False

def send_email_notification(to_email, subject, body):
    """Send email notification"""
    if not ENABLE_EMAIL or not SENDER_EMAIL or not SENDER_PASSWORD:
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

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

def photographer_required(f):
    """Decorator for photographer-only routes"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') not in ['photographer', 'admin']:
            flash('Photographer access required')
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
        data = request.form if request.form else request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'client')  # client, photographer, admin
        
        if not all([username, email, password]):
            flash('All fields are required')
            return render_template('register.html') if request.form else jsonify({'error': 'All fields required'}), 400
        
        # Check if user already exists
        try:
            response = users_table.get_item(Key={'email': email})
            if 'Item' in response:
                flash('User already exists')
                return render_template('register.html') if request.form else jsonify({'error': 'User exists'}), 409
        except Exception as e:
            print(f"❌ Error checking existing user: {e}")
            flash('Database error')
            return render_template('register.html') if request.form else jsonify({'error': str(e)}), 500
        
        # Create new user
        user_id = str(uuid.uuid4())
        hashed_password = generate_password_hash(password)
        
        try:
            users_table.put_item(Item={
                'user_id': user_id,
                'email': email,
                'username': username,
                'password': hashed_password,
                'role': role,
                'created_at': datetime.now().isoformat(),
                'is_active': True
            })
            
            flash('Registration successful')
            if request.form:
                return redirect(url_for('login'))
            else:
                return jsonify({'message': 'User created successfully', 'user_id': user_id}), 201
                
        except Exception as e:
            print(f"❌ Error saving user to DynamoDB: {e}")
            flash('Registration failed')
            return render_template('register.html') if request.form else jsonify({'error': str(e)}), 500
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form if request.form else request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not all([email, password]):
            flash('Email and password required')
            return render_template('login.html') if request.form else jsonify({'error': 'Missing credentials'}), 400
        
        try:
            response = users_table.get_item(Key={'email': email})
            if 'Item' not in response:
                flash('Invalid credentials')
                return render_template('login.html') if request.form else jsonify({'error': 'Invalid credentials'}), 401
            
            user = response['Item']
            if not user.get('is_active', True):
                flash('Account deactivated')
                return render_template('login.html') if request.form else jsonify({'error': 'Account deactivated'}), 401
            
            if check_password_hash(user['password'], password):
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                session['email'] = user['email']
                session['user_role'] = user.get('role', 'client')
                
                if request.form:
                    return redirect(url_for('dashboard'))
                else:
                    return jsonify({
                        'message': 'Login successful',
                        'user': {
                            'user_id': user['user_id'],
                            'username': user['username'],
                            'email': user['email'],
                            'role': user.get('role', 'client')
                        }
                    }), 200
            else:
                flash('Invalid credentials')
                return render_template('login.html') if request.form else jsonify({'error': 'Invalid credentials'}), 401
                
        except Exception as e:
            flash('Login failed')
            return render_template('login.html') if request.form else jsonify({'error': str(e)}), 500
    
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

# ---------------------------------------
# Client Dashboard Routes
# ---------------------------------------
@app.route('/client/dashboard')
@login_required
def client_dashboard():
    try:
        # Get available photographers
        photographers_response = photographers_table.scan(
            FilterExpression='is_active = :active',
            ExpressionAttributeValues={':active': True},
            Limit=10
        )
        photographers = photographers_response.get('Items', [])

        # Get user's recent bookings
        user_bookings_response = bookings_table.query(
            IndexName='UserIndex',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': session['user_id']},
            Limit=5,
            ScanIndexForward=False
        )
        user_bookings = user_bookings_response.get('Items', [])

        return render_template('client_dashboard.html',
                             photographers=photographers,
                             user_bookings=user_bookings)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}')
        return render_template('client_dashboard.html', photographers=[], user_bookings=[])

# ---------------------------------------
# Photographer Dashboard Routes
# ---------------------------------------
@app.route('/photographer/dashboard')
@photographer_required
def photographer_dashboard():
    try:
        # Get photographer's profile
        photographer_response = photographers_table.get_item(
            Key={'photographer_id': session['user_id']}
        )
        photographer_profile = photographer_response.get('Item', {})

        # Get pending booking requests
        pending_bookings_response = bookings_table.query(
            IndexName='PhotographerIndex',
            KeyConditionExpression='photographer_id = :photographer_id',
            FilterExpression='booking_status = :status',
            ExpressionAttributeValues={
                ':photographer_id': session['user_id'],
                ':status': 'pending'
            },
            Limit=10
        )
        pending_bookings = pending_bookings_response.get('Items', [])

        # Get confirmed bookings for next 30 days
        future_date = (datetime.now() + timedelta(days=30)).isoformat()
        confirmed_bookings_response = bookings_table.query(
            IndexName='PhotographerIndex',
            KeyConditionExpression='photographer_id = :photographer_id',
            FilterExpression='booking_status = :status AND event_date <= :future_date',
            ExpressionAttributeValues={
                ':photographer_id': session['user_id'],
                ':status': 'confirmed',
                ':future_date': future_date
            },
            Limit=10
        )
        confirmed_bookings = confirmed_bookings_response.get('Items', [])

        return render_template('photographer_dashboard.html',
                             photographer_profile=photographer_profile,
                             pending_bookings=pending_bookings,
                             confirmed_bookings=confirmed_bookings)
    except Exception as e:
        flash(f'Error loading photographer dashboard: {str(e)}')
        return render_template('photographer_dashboard.html',
                             photographer_profile={},
                             pending_bookings=[],
                             confirmed_bookings=[])

# ---------------------------------------
# Admin Dashboard Routes
# ---------------------------------------
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    try:
        # Get recent bookings with analytics
        bookings_response = bookings_table.scan(Limit=20)
        bookings = bookings_response.get('Items', [])

        # Get feedback stats
        feedback_response = feedback_table.scan()
        feedback_items = feedback_response.get('Items', [])

        # Calculate booking statistics
        booking_stats = {'pending': 0, 'confirmed': 0, 'completed': 0, 'cancelled': 0}
        for booking in bookings:
            status = booking.get('booking_status', 'pending')
            if status in booking_stats:
                booking_stats[status] += 1

        # Calculate sentiment statistics
        sentiment_stats = {'positive': 0, 'negative': 0, 'neutral': 0}
        for feedback in feedback_items:
            sentiment = feedback.get('sentiment', 'neutral')
            if sentiment in sentiment_stats:
                sentiment_stats[sentiment] += 1

        # Get negative feedback count
        negative_feedback = [f for f in feedback_items if f.get('sentiment') == 'negative']

        return render_template('admin_dashboard.html',
                             bookings=bookings,
                             booking_stats=booking_stats,
                             sentiment_stats=sentiment_stats,
                             negative_feedback=negative_feedback,
                             total_bookings=len(bookings))
    except Exception as e:
        flash(f'Error loading admin dashboard: {str(e)}')
        return render_template('admin_dashboard.html',
                             bookings=[],
                             booking_stats={'pending': 0, 'confirmed': 0, 'completed': 0, 'cancelled': 0},
                             sentiment_stats={'positive': 0, 'negative': 0, 'neutral': 0},
                             negative_feedback=[],
                             total_bookings=0)

# ---------------------------------------
# Photographer Routes
# ---------------------------------------
@app.route('/photographers')
@login_required
def photographers():
    try:
        # Get all active photographers
        response = photographers_table.scan(
            FilterExpression='is_active = :active',
            ExpressionAttributeValues={':active': True}
        )
        photographers_list = response.get('Items', [])

        # Get filter parameters
        specialization = request.args.get('specialization', '')
        location = request.args.get('location', '')

        # Apply filters if provided
        if specialization:
            photographers_list = [p for p in photographers_list if p.get('specialization', '').lower() == specialization.lower()]
        if location:
            photographers_list = [p for p in photographers_list if location.lower() in p.get('location', '').lower()]

        return render_template('photographers.html', photographers=photographers_list)
    except Exception as e:
        flash(f'Error loading photographers: {str(e)}')
        return render_template('photographers.html', photographers=[])

@app.route('/photographer/<photographer_id>')
@login_required
def photographer_profile(photographer_id):
    try:
        # Get photographer details
        response = photographers_table.get_item(Key={'photographer_id': photographer_id})
        photographer = response.get('Item')

        if not photographer:
            flash('Photographer not found')
            return redirect(url_for('photographers'))

        return render_template('photographer_detail.html', photographer=photographer)
    except Exception as e:
        flash(f'Error loading photographer profile: {str(e)}')
        return redirect(url_for('photographers'))

# ---------------------------------------
# Booking Routes
# ---------------------------------------
@app.route('/book/<photographer_id>', methods=['GET', 'POST'])
@login_required
def book_photographer(photographer_id):
    if request.method == 'POST':
        try:
            data = request.form
            event_date = data.get('event_date')
            event_time = data.get('event_time')
            event_type = data.get('event_type')
            location = data.get('location')
            duration = data.get('duration', '2')
            special_requirements = data.get('special_requirements', '')

            if not all([event_date, event_time, event_type, location]):
                flash('All required fields must be filled')
                return redirect(url_for('book_photographer', photographer_id=photographer_id))

            # Check if photographer is available on the requested date
            existing_bookings = bookings_table.query(
                IndexName='PhotographerIndex',
                KeyConditionExpression='photographer_id = :photographer_id AND event_date = :event_date',
                FilterExpression='booking_status IN (:confirmed, :pending)',
                ExpressionAttributeValues={
                    ':photographer_id': photographer_id,
                    ':event_date': event_date,
                    ':confirmed': 'confirmed',
                    ':pending': 'pending'
                }
            )

            if existing_bookings.get('Items'):
                flash('Photographer is not available on the selected date')
                return redirect(url_for('book_photographer', photographer_id=photographer_id))

            # Create booking
            booking_id = str(uuid.uuid4())
            booking_data = {
                'booking_id': booking_id,
                'user_id': session['user_id'],
                'photographer_id': photographer_id,
                'event_date': event_date,
                'event_time': event_time,
                'event_type': event_type,
                'location': location,
                'duration': int(duration),
                'special_requirements': special_requirements,
                'booking_status': 'pending',
                'created_at': datetime.now().isoformat(),
                'client_name': session['username'],
                'client_email': session['email']
            }

            bookings_table.put_item(Item=booking_data)

            # Send notification to photographer (if SNS is enabled)
            if ENABLE_SNS and SNS_TOPIC_ARN:
                message = f"New booking request!\nClient: {session['username']}\nEvent: {event_type}\nDate: {event_date}\nLocation: {location}"
                send_sns_alert(message, "New Booking Request")

            flash('Booking request submitted successfully! The photographer will review and respond soon.')
            return redirect(url_for('my_bookings'))

        except Exception as e:
            flash(f'Error creating booking: {str(e)}')
            return redirect(url_for('book_photographer', photographer_id=photographer_id))

    # GET request - show booking form
    try:
        photographer_response = photographers_table.get_item(Key={'photographer_id': photographer_id})
        photographer = photographer_response.get('Item')

        if not photographer:
            flash('Photographer not found')
            return redirect(url_for('photographers'))

        return render_template('book_photographer.html', photographer=photographer)
    except Exception as e:
        flash(f'Error loading booking form: {str(e)}')
        return redirect(url_for('photographers'))

@app.route('/my-bookings')
@login_required
def my_bookings():
    try:
        # Get user's bookings
        response = bookings_table.query(
            IndexName='UserIndex',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': session['user_id']},
            ScanIndexForward=False
        )
        bookings = response.get('Items', [])

        return render_template('my_bookings.html', bookings=bookings)
    except Exception as e:
        flash(f'Error loading bookings: {str(e)}')
        return render_template('my_bookings.html', bookings=[])

# ---------------------------------------
# Feedback Routes
# ---------------------------------------
@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        data = request.form
        feedback_type = data.get('feedback_type', 'general')
        subject = data.get('subject')
        message = data.get('message')

        if not all([subject, message]):
            flash('Subject and message are required')
            return render_template('feedback.html')

        # Analyze sentiment
        sentiment, sentiment_score = analyze_sentiment(message)
        feedback_id = str(uuid.uuid4())

        try:
            feedback_table.put_item(Item={
                'feedback_id': feedback_id,
                'user_id': session['user_id'],
                'username': session['username'],
                'feedback_type': feedback_type,
                'subject': subject,
                'message': message,
                'sentiment': sentiment,
                'sentiment_score': float(sentiment_score),
                'status': 'open',
                'created_at': datetime.now().isoformat()
            })

            # Send alert for negative feedback
            if sentiment == 'negative':
                alert_message = f"Negative feedback received!\nType: {feedback_type}\nUser: {session['username']}\nSubject: {subject}\nMessage: {message[:100]}..."
                send_sns_alert(alert_message, "Negative Customer Feedback Alert")

            flash('Feedback submitted successfully')
            return redirect(url_for('dashboard'))

        except Exception as e:
            flash('Failed to submit feedback')
            return render_template('feedback.html')

    return render_template('feedback.html')

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
    # Use SocketIO for real-time features
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
