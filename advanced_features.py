"""
Advanced Features Module for Capture Moments
Includes: Real-time chat, Payment integration, Photo gallery, Review system, Advanced analytics
"""

import os
import boto3
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import uuid
from decimal import Decimal
import stripe
from textblob import TextBlob
import numpy as np
from collections import defaultdict

# Create Blueprint for advanced features
advanced_bp = Blueprint('advanced', __name__)

# AWS S3 for photo storage
s3_client = boto3.client('s3', region_name=os.environ.get('AWS_REGION_NAME', 'ap-south-1'))
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'capture-moments-photos')

# Stripe configuration for payments
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')

# DynamoDB tables for advanced features
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION_NAME', 'ap-south-1'))
reviews_table = dynamodb.Table('CaptureMomentsReviews')
galleries_table = dynamodb.Table('CaptureMomentsGalleries')
messages_table = dynamodb.Table('CaptureMomentsMessages')
payments_table = dynamodb.Table('CaptureMomentsPayments')

# ---------------------------------------
# Photo Gallery System
# ---------------------------------------

@advanced_bp.route('/gallery/<photographer_id>')
def photographer_gallery(photographer_id):
    """Display photographer's photo gallery"""
    try:
        # Get gallery items for photographer
        response = galleries_table.query(
            IndexName='PhotographerIndex',
            KeyConditionExpression='photographer_id = :photographer_id',
            ExpressionAttributeValues={':photographer_id': photographer_id},
            ScanIndexForward=False
        )
        gallery_items = response.get('Items', [])
        
        # Group by categories
        categorized_photos = defaultdict(list)
        for item in gallery_items:
            category = item.get('category', 'general')
            categorized_photos[category].append(item)
        
        return render_template('photographer_gallery.html', 
                             photographer_id=photographer_id,
                             categorized_photos=dict(categorized_photos))
    except Exception as e:
        flash(f'Error loading gallery: {str(e)}')
        return redirect(url_for('photographer_profile', photographer_id=photographer_id))

@advanced_bp.route('/upload-photos/<photographer_id>', methods=['GET', 'POST'])
def upload_photos(photographer_id):
    """Upload photos to photographer's gallery"""
    if session.get('user_role') not in ['photographer', 'admin'] or \
       (session.get('user_role') == 'photographer' and session.get('user_id') != photographer_id):
        flash('Unauthorized access')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            files = request.files.getlist('photos')
            category = request.form.get('category', 'general')
            description = request.form.get('description', '')
            
            uploaded_count = 0
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    file_key = f"galleries/{photographer_id}/{uuid.uuid4()}_{filename}"
                    
                    # Upload to S3
                    s3_client.upload_fileobj(
                        file,
                        BUCKET_NAME,
                        file_key,
                        ExtraArgs={'ContentType': file.content_type}
                    )
                    
                    # Save to DynamoDB
                    gallery_id = str(uuid.uuid4())
                    galleries_table.put_item(Item={
                        'gallery_id': gallery_id,
                        'photographer_id': photographer_id,
                        'file_key': file_key,
                        'filename': filename,
                        'category': category,
                        'description': description,
                        'upload_date': datetime.now().isoformat(),
                        'file_size': len(file.read()),
                        'content_type': file.content_type
                    })
                    uploaded_count += 1
            
            flash(f'Successfully uploaded {uploaded_count} photos')
            return redirect(url_for('advanced.photographer_gallery', photographer_id=photographer_id))
            
        except Exception as e:
            flash(f'Error uploading photos: {str(e)}')
    
    return render_template('upload_photos.html', photographer_id=photographer_id)

# ---------------------------------------
# Review and Rating System
# ---------------------------------------

@advanced_bp.route('/add-review/<booking_id>', methods=['GET', 'POST'])
def add_review(booking_id):
    """Add review for completed booking"""
    if request.method == 'POST':
        try:
            data = request.form
            rating = int(data.get('rating'))
            review_text = data.get('review_text', '')
            service_quality = int(data.get('service_quality', 5))
            communication = int(data.get('communication', 5))
            value_for_money = int(data.get('value_for_money', 5))
            
            # Analyze sentiment
            sentiment, sentiment_score = analyze_sentiment(review_text)
            
            # Calculate overall score
            overall_score = (rating + service_quality + communication + value_for_money) / 4
            
            review_id = str(uuid.uuid4())
            reviews_table.put_item(Item={
                'review_id': review_id,
                'booking_id': booking_id,
                'user_id': session['user_id'],
                'photographer_id': data.get('photographer_id'),
                'rating': rating,
                'review_text': review_text,
                'service_quality': service_quality,
                'communication': communication,
                'value_for_money': value_for_money,
                'overall_score': Decimal(str(overall_score)),
                'sentiment': sentiment,
                'sentiment_score': Decimal(str(sentiment_score)),
                'created_at': datetime.now().isoformat(),
                'is_verified': True  # Since it's from a completed booking
            })
            
            flash('Review submitted successfully!')
            return redirect(url_for('my_bookings'))
            
        except Exception as e:
            flash(f'Error submitting review: {str(e)}')
    
    return render_template('add_review.html', booking_id=booking_id)

@advanced_bp.route('/reviews/<photographer_id>')
def photographer_reviews(photographer_id):
    """Display all reviews for a photographer"""
    try:
        response = reviews_table.query(
            IndexName='PhotographerIndex',
            KeyConditionExpression='photographer_id = :photographer_id',
            ExpressionAttributeValues={':photographer_id': photographer_id},
            ScanIndexForward=False
        )
        reviews = response.get('Items', [])
        
        # Calculate statistics
        if reviews:
            total_reviews = len(reviews)
            avg_rating = sum(float(r.get('rating', 0)) for r in reviews) / total_reviews
            avg_service = sum(float(r.get('service_quality', 0)) for r in reviews) / total_reviews
            avg_communication = sum(float(r.get('communication', 0)) for r in reviews) / total_reviews
            avg_value = sum(float(r.get('value_for_money', 0)) for r in reviews) / total_reviews
            
            # Rating distribution
            rating_distribution = defaultdict(int)
            for review in reviews:
                rating_distribution[int(review.get('rating', 0))] += 1
        else:
            total_reviews = 0
            avg_rating = avg_service = avg_communication = avg_value = 0
            rating_distribution = {}
        
        stats = {
            'total_reviews': total_reviews,
            'avg_rating': round(avg_rating, 1),
            'avg_service': round(avg_service, 1),
            'avg_communication': round(avg_communication, 1),
            'avg_value': round(avg_value, 1),
            'rating_distribution': dict(rating_distribution)
        }
        
        return render_template('photographer_reviews.html', 
                             photographer_id=photographer_id,
                             reviews=reviews,
                             stats=stats)
    except Exception as e:
        flash(f'Error loading reviews: {str(e)}')
        return redirect(url_for('photographer_profile', photographer_id=photographer_id))

# ---------------------------------------
# Payment Integration
# ---------------------------------------

@advanced_bp.route('/payment/<booking_id>')
def payment_page(booking_id):
    """Payment page for booking"""
    try:
        # Get booking details
        from app import bookings_table
        response = bookings_table.get_item(Key={'booking_id': booking_id})
        booking = response.get('Item')
        
        if not booking or booking.get('user_id') != session['user_id']:
            flash('Booking not found or unauthorized')
            return redirect(url_for('my_bookings'))
        
        # Calculate amount (this would typically come from photographer's pricing)
        base_price = 5000  # Base price in cents ($50.00)
        duration_multiplier = int(booking.get('duration', 2))
        total_amount = base_price * duration_multiplier
        
        return render_template('payment.html', 
                             booking=booking,
                             amount=total_amount,
                             stripe_key=STRIPE_PUBLISHABLE_KEY)
    except Exception as e:
        flash(f'Error loading payment page: {str(e)}')
        return redirect(url_for('my_bookings'))

@advanced_bp.route('/process-payment', methods=['POST'])
def process_payment():
    """Process Stripe payment"""
    try:
        data = request.get_json()
        booking_id = data.get('booking_id')
        payment_method_id = data.get('payment_method_id')
        amount = int(data.get('amount'))
        
        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            payment_method=payment_method_id,
            confirmation_method='manual',
            confirm=True,
            metadata={'booking_id': booking_id}
        )
        
        if intent.status == 'succeeded':
            # Save payment record
            payment_id = str(uuid.uuid4())
            payments_table.put_item(Item={
                'payment_id': payment_id,
                'booking_id': booking_id,
                'user_id': session['user_id'],
                'amount': amount,
                'currency': 'usd',
                'stripe_payment_intent_id': intent.id,
                'status': 'completed',
                'created_at': datetime.now().isoformat()
            })
            
            # Update booking status
            from app import bookings_table
            bookings_table.update_item(
                Key={'booking_id': booking_id},
                UpdateExpression='SET booking_status = :status, payment_status = :payment_status',
                ExpressionAttributeValues={
                    ':status': 'confirmed',
                    ':payment_status': 'paid'
                }
            )
            
            return jsonify({'success': True, 'message': 'Payment successful!'})
        else:
            return jsonify({'success': False, 'message': 'Payment failed'})
            
    except stripe.error.StripeError as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error processing payment: {str(e)}'})

def analyze_sentiment(text):
    """Analyze sentiment using TextBlob"""
    if not text:
        return 'neutral', 0.0
    
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    
    if polarity > 0.1:
        return 'positive', polarity
    elif polarity < -0.1:
        return 'negative', polarity
    else:
        return 'neutral', polarity
