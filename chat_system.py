"""
Real-time Chat System for Capture Moments
Includes: WebSocket-based messaging, Chat rooms, File sharing, Message history
"""

import os
import boto3
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, session
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
import uuid
from werkzeug.utils import secure_filename

# Create Blueprint for chat system
chat_bp = Blueprint('chat', __name__)

# AWS services
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION_NAME', 'ap-south-1'))
s3_client = boto3.client('s3', region_name=os.environ.get('AWS_REGION_NAME', 'ap-south-1'))

# DynamoDB tables
messages_table = dynamodb.Table('CaptureMomentsMessages')
chat_rooms_table = dynamodb.Table('CaptureMonentsChatRooms')

# S3 bucket for file sharing
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'capture-moments-files')

# Global SocketIO instance (to be initialized in main app)
socketio = None

def init_socketio(app):
    """Initialize SocketIO with the Flask app"""
    global socketio
    socketio = SocketIO(app, cors_allowed_origins="*")
    register_socket_events()
    return socketio

# ---------------------------------------
# Chat Room Management
# ---------------------------------------

@chat_bp.route('/chat/<booking_id>')
def chat_room(booking_id):
    """Chat room for a specific booking"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        # Verify user has access to this booking
        from app import bookings_table
        booking_response = bookings_table.get_item(Key={'booking_id': booking_id})
        booking = booking_response.get('Item')
        
        if not booking:
            flash('Booking not found')
            return redirect(url_for('dashboard'))
        
        # Check if user is either the client or photographer
        user_id = session['user_id']
        if user_id not in [booking.get('user_id'), booking.get('photographer_id')]:
            flash('Unauthorized access to chat')
            return redirect(url_for('dashboard'))
        
        # Get or create chat room
        room_id = f"booking_{booking_id}"
        chat_room_data = get_or_create_chat_room(room_id, booking_id, user_id)
        
        # Get message history
        messages = get_message_history(room_id)
        
        return render_template('chat_room.html', 
                             booking=booking,
                             room_id=room_id,
                             messages=messages,
                             current_user_id=user_id)
        
    except Exception as e:
        flash(f'Error accessing chat: {str(e)}')
        return redirect(url_for('dashboard'))

def get_or_create_chat_room(room_id, booking_id, user_id):
    """Get existing chat room or create new one"""
    try:
        # Check if room exists
        response = chat_rooms_table.get_item(Key={'room_id': room_id})
        
        if 'Item' not in response:
            # Create new chat room
            chat_room_data = {
                'room_id': room_id,
                'booking_id': booking_id,
                'created_by': user_id,
                'created_at': datetime.now().isoformat(),
                'is_active': True,
                'participants': []
            }
            chat_rooms_table.put_item(Item=chat_room_data)
            return chat_room_data
        
        return response['Item']
        
    except Exception as e:
        print(f"Error managing chat room: {e}")
        return None

def get_message_history(room_id, limit=50):
    """Get message history for a chat room"""
    try:
        response = messages_table.query(
            IndexName='RoomIndex',
            KeyConditionExpression='room_id = :room_id',
            ExpressionAttributeValues={':room_id': room_id},
            ScanIndexForward=False,
            Limit=limit
        )
        
        messages = response.get('Items', [])
        # Reverse to show oldest first
        return list(reversed(messages))
        
    except Exception as e:
        print(f"Error getting message history: {e}")
        return []

# ---------------------------------------
# WebSocket Events
# ---------------------------------------

def register_socket_events():
    """Register all socket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        if 'user_id' not in session:
            return False  # Reject connection
        
        print(f"User {session['user_id']} connected")
        emit('status', {'msg': f"{session['username']} has connected"})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        if 'user_id' in session:
            print(f"User {session['user_id']} disconnected")
    
    @socketio.on('join_room')
    def handle_join_room(data):
        """Handle user joining a chat room"""
        if 'user_id' not in session:
            return
        
        room_id = data['room']
        join_room(room_id)
        
        # Add user to room participants
        try:
            chat_rooms_table.update_item(
                Key={'room_id': room_id},
                UpdateExpression='ADD participants :user_id',
                ExpressionAttributeValues={':user_id': {session['user_id']}}
            )
        except Exception as e:
            print(f"Error updating room participants: {e}")
        
        emit('status', {
            'msg': f"{session['username']} joined the chat",
            'user_id': session['user_id']
        }, room=room_id)
    
    @socketio.on('leave_room')
    def handle_leave_room(data):
        """Handle user leaving a chat room"""
        if 'user_id' not in session:
            return
        
        room_id = data['room']
        leave_room(room_id)
        
        emit('status', {
            'msg': f"{session['username']} left the chat",
            'user_id': session['user_id']
        }, room=room_id)
    
    @socketio.on('send_message')
    def handle_send_message(data):
        """Handle sending a message"""
        if 'user_id' not in session:
            return
        
        room_id = data['room']
        message_text = data['message']
        message_type = data.get('type', 'text')
        
        # Save message to database
        message_id = str(uuid.uuid4())
        message_data = {
            'message_id': message_id,
            'room_id': room_id,
            'user_id': session['user_id'],
            'username': session['username'],
            'message_text': message_text,
            'message_type': message_type,
            'timestamp': datetime.now().isoformat(),
            'is_read': False
        }
        
        try:
            messages_table.put_item(Item=message_data)
            
            # Emit message to room
            emit('receive_message', {
                'message_id': message_id,
                'user_id': session['user_id'],
                'username': session['username'],
                'message': message_text,
                'type': message_type,
                'timestamp': message_data['timestamp']
            }, room=room_id)
            
        except Exception as e:
            print(f"Error saving message: {e}")
            emit('error', {'msg': 'Failed to send message'})
    
    @socketio.on('typing')
    def handle_typing(data):
        """Handle typing indicator"""
        if 'user_id' not in session:
            return
        
        room_id = data['room']
        is_typing = data['typing']
        
        emit('user_typing', {
            'user_id': session['user_id'],
            'username': session['username'],
            'typing': is_typing
        }, room=room_id, include_self=False)
    
    @socketio.on('mark_read')
    def handle_mark_read(data):
        """Mark messages as read"""
        if 'user_id' not in session:
            return
        
        message_ids = data.get('message_ids', [])
        
        try:
            for message_id in message_ids:
                messages_table.update_item(
                    Key={'message_id': message_id},
                    UpdateExpression='SET is_read = :read',
                    ExpressionAttributeValues={':read': True}
                )
        except Exception as e:
            print(f"Error marking messages as read: {e}")

# ---------------------------------------
# File Sharing
# ---------------------------------------

@chat_bp.route('/upload-file/<room_id>', methods=['POST'])
def upload_file(room_id):
    """Upload file to chat room"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Secure filename
        filename = secure_filename(file.filename)
        file_key = f"chat_files/{room_id}/{uuid.uuid4()}_{filename}"
        
        # Upload to S3
        s3_client.upload_fileobj(
            file,
            BUCKET_NAME,
            file_key,
            ExtraArgs={'ContentType': file.content_type}
        )
        
        # Generate presigned URL for download
        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': file_key},
            ExpiresIn=3600  # 1 hour
        )
        
        # Save file message to database
        message_id = str(uuid.uuid4())
        message_data = {
            'message_id': message_id,
            'room_id': room_id,
            'user_id': session['user_id'],
            'username': session['username'],
            'message_text': f"Shared file: {filename}",
            'message_type': 'file',
            'file_url': download_url,
            'file_name': filename,
            'file_size': len(file.read()),
            'timestamp': datetime.now().isoformat(),
            'is_read': False
        }
        
        messages_table.put_item(Item=message_data)
        
        # Emit file message to room
        if socketio:
            socketio.emit('receive_message', {
                'message_id': message_id,
                'user_id': session['user_id'],
                'username': session['username'],
                'message': f"Shared file: {filename}",
                'type': 'file',
                'file_url': download_url,
                'file_name': filename,
                'timestamp': message_data['timestamp']
            }, room=room_id)
        
        return jsonify({
            'success': True,
            'message_id': message_id,
            'download_url': download_url
        })
        
    except Exception as e:
        return jsonify({'error': f'File upload failed: {str(e)}'}), 500

# ---------------------------------------
# Chat API Endpoints
# ---------------------------------------

@chat_bp.route('/api/chat/rooms')
def get_user_chat_rooms():
    """Get all chat rooms for current user"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Get user's bookings to find associated chat rooms
        from app import bookings_table
        user_bookings = bookings_table.query(
            IndexName='UserIndex',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': session['user_id']}
        )
        
        # Also get bookings where user is the photographer
        photographer_bookings = bookings_table.query(
            IndexName='PhotographerIndex',
            KeyConditionExpression='photographer_id = :photographer_id',
            ExpressionAttributeValues={':photographer_id': session['user_id']}
        )
        
        all_bookings = user_bookings.get('Items', []) + photographer_bookings.get('Items', [])
        
        chat_rooms = []
        for booking in all_bookings:
            room_id = f"booking_{booking['booking_id']}"
            
            # Get latest message for preview
            latest_messages = messages_table.query(
                IndexName='RoomIndex',
                KeyConditionExpression='room_id = :room_id',
                ExpressionAttributeValues={':room_id': room_id},
                ScanIndexForward=False,
                Limit=1
            )
            
            latest_message = latest_messages.get('Items', [{}])[0] if latest_messages.get('Items') else {}
            
            chat_rooms.append({
                'room_id': room_id,
                'booking_id': booking['booking_id'],
                'event_type': booking.get('event_type', ''),
                'event_date': booking.get('event_date', ''),
                'latest_message': latest_message.get('message_text', ''),
                'latest_timestamp': latest_message.get('timestamp', ''),
                'unread_count': 0  # Would need to implement unread counting
            })
        
        return jsonify({'chat_rooms': chat_rooms})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/api/chat/messages/<room_id>')
def get_room_messages(room_id):
    """Get messages for a specific room"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        messages = get_message_history(room_id, limit=100)
        return jsonify({'messages': messages})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
