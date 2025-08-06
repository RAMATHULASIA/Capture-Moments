"""
Demo Data Setup for Capture Moments
Creates sample users, photographers, and bookings for testing
"""

import os
import boto3
import uuid
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS Configuration
AWS_REGION_NAME = os.environ.get('AWS_REGION_NAME', 'ap-south-1')

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION_NAME)

# Tables
users_table = dynamodb.Table('CaptureMomentsUsers')
photographers_table = dynamodb.Table('CaptureMomentsPhotographers')
bookings_table = dynamodb.Table('CaptureMomentsBookings')

def create_demo_users():
    """Create demo users for testing"""
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
        try:
            users_table.put_item(Item=user)
            print(f"✅ Created user: {user['email']}")
        except Exception as e:
            print(f"❌ Error creating user {user['email']}: {e}")
    
    return demo_users

def create_demo_photographers():
    """Create demo photographers"""
    demo_photographers = [
        {
            'photographer_id': str(uuid.uuid4()),
            'name': 'Rajesh Kumar',
            'email': 'rajesh@capturemoments.com',
            'specialization': 'wedding',
            'location': 'Hyderabad',
            'bio': 'Professional wedding photographer with 8+ years experience',
            'years_experience': 8,
            'price_range': 'premium',
            'average_rating': 4.8,
            'is_active': True,
            'created_at': datetime.now().isoformat()
        },
        {
            'photographer_id': str(uuid.uuid4()),
            'name': 'Priya Sharma',
            'email': 'priya@capturemoments.com',
            'specialization': 'portrait',
            'location': 'Mumbai',
            'bio': 'Creative portrait photographer specializing in family and individual sessions',
            'years_experience': 5,
            'price_range': 'medium',
            'average_rating': 4.6,
            'is_active': True,
            'created_at': datetime.now().isoformat()
        },
        {
            'photographer_id': str(uuid.uuid4()),
            'name': 'Amit Patel',
            'email': 'amit@capturemoments.com',
            'specialization': 'event',
            'location': 'Delhi',
            'bio': 'Corporate and social event photographer with modern style',
            'years_experience': 6,
            'price_range': 'medium',
            'average_rating': 4.7,
            'is_active': True,
            'created_at': datetime.now().isoformat()
        }
    ]
    
    for photographer in demo_photographers:
        try:
            photographers_table.put_item(Item=photographer)
            print(f"✅ Created photographer: {photographer['name']}")
        except Exception as e:
            print(f"❌ Error creating photographer {photographer['name']}: {e}")
    
    return demo_photographers

def create_demo_bookings(users, photographers):
    """Create demo bookings"""
    client_user = next(u for u in users if u['role'] == 'client')
    
    demo_bookings = [
        {
            'booking_id': str(uuid.uuid4()),
            'user_id': client_user['user_id'],
            'photographer_id': photographers[0]['photographer_id'],
            'event_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'event_time': '16:00',
            'event_type': 'wedding',
            'location': 'Hyderabad, India',
            'duration': 6,
            'special_requirements': 'Traditional Indian wedding ceremony',
            'booking_status': 'confirmed',
            'created_at': datetime.now().isoformat(),
            'client_name': client_user['username'],
            'client_email': client_user['email']
        },
        {
            'booking_id': str(uuid.uuid4()),
            'user_id': client_user['user_id'],
            'photographer_id': photographers[1]['photographer_id'],
            'event_date': (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),
            'event_time': '10:00',
            'event_type': 'portrait',
            'location': 'Mumbai, India',
            'duration': 2,
            'special_requirements': 'Family portrait session',
            'booking_status': 'pending',
            'created_at': datetime.now().isoformat(),
            'client_name': client_user['username'],
            'client_email': client_user['email']
        }
    ]
    
    for booking in demo_bookings:
        try:
            bookings_table.put_item(Item=booking)
            print(f"✅ Created booking: {booking['event_type']} on {booking['event_date']}")
        except Exception as e:
            print(f"❌ Error creating booking: {e}")
    
    return demo_bookings

def setup_demo_data():
    """Setup all demo data"""
    print("🚀 Setting up demo data for Capture Moments...")
    print("=" * 50)
    
    try:
        # Create demo users
        users = create_demo_users()
        
        # Create demo photographers
        photographers = create_demo_photographers()
        
        # Create demo bookings
        bookings = create_demo_bookings(users, photographers)
        
        print("=" * 50)
        print("✅ Demo data setup completed!")
        print("\n📝 Demo Accounts:")
        print("Client: client@demo.com / demo123")
        print("Photographer: photographer@demo.com / demo123")
        print("Admin: admin@demo.com / demo123")
        
    except Exception as e:
        print(f"❌ Error setting up demo data: {e}")

if __name__ == "__main__":
    setup_demo_data()
