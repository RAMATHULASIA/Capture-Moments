"""
AI-Powered Features Module for Capture Moments
Includes: Smart recommendations, Automated pricing, Intelligent scheduling, Demand prediction
"""

import os
import boto3
import json
import numpy as np
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template, session
from collections import defaultdict, Counter
import math
from textblob import TextBlob
import random

# Create Blueprint for AI features
ai_bp = Blueprint('ai', __name__)

# AWS services
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION_NAME', 'ap-south-1'))
comprehend = boto3.client('comprehend', region_name=os.environ.get('AWS_REGION_NAME', 'ap-south-1'))

# DynamoDB tables
bookings_table = dynamodb.Table('CaptureMomentsBookings')
photographers_table = dynamodb.Table('CaptureMomentsPhotographers')
reviews_table = dynamodb.Table('CaptureMomentsReviews')
users_table = dynamodb.Table('CaptureMomentsUsers')

# ---------------------------------------
# Smart Photographer Recommendations
# ---------------------------------------

class RecommendationEngine:
    def __init__(self):
        self.user_preferences = {}
        self.photographer_features = {}
        self.booking_history = {}
    
    def load_data(self):
        """Load data for recommendation engine"""
        try:
            # Load user booking history
            bookings_response = bookings_table.scan()
            bookings = bookings_response.get('Items', [])
            
            # Load photographer data
            photographers_response = photographers_table.scan()
            photographers = photographers_response.get('Items', [])
            
            # Load reviews
            reviews_response = reviews_table.scan()
            reviews = reviews_response.get('Items', [])
            
            return bookings, photographers, reviews
        except Exception as e:
            print(f"Error loading data: {e}")
            return [], [], []
    
    def calculate_photographer_score(self, photographer, user_preferences, reviews):
        """Calculate photographer score based on various factors"""
        score = 0.0
        
        # Base score from reviews
        photographer_reviews = [r for r in reviews if r.get('photographer_id') == photographer.get('photographer_id')]
        if photographer_reviews:
            avg_rating = sum(float(r.get('rating', 0)) for r in photographer_reviews) / len(photographer_reviews)
            score += avg_rating * 0.3
        else:
            score += 3.0 * 0.3  # Default score for new photographers
        
        # Specialization match
        user_event_type = user_preferences.get('event_type', '').lower()
        photographer_specialization = photographer.get('specialization', '').lower()
        if user_event_type in photographer_specialization or photographer_specialization in user_event_type:
            score += 2.0
        
        # Location proximity (simplified)
        user_location = user_preferences.get('location', '').lower()
        photographer_location = photographer.get('location', '').lower()
        if user_location in photographer_location or photographer_location in user_location:
            score += 1.5
        
        # Experience factor
        years_experience = photographer.get('years_experience', 1)
        score += min(years_experience * 0.1, 1.0)
        
        # Availability factor
        if photographer.get('is_active', False):
            score += 0.5
        
        return score
    
    def get_recommendations(self, user_id, event_type=None, location=None, limit=10):
        """Get personalized photographer recommendations"""
        try:
            bookings, photographers, reviews = self.load_data()
            
            # Get user preferences from booking history
            user_bookings = [b for b in bookings if b.get('user_id') == user_id]
            user_preferences = {
                'event_type': event_type or (user_bookings[-1].get('event_type') if user_bookings else ''),
                'location': location or (user_bookings[-1].get('location') if user_bookings else ''),
                'budget_range': 'medium'  # Could be inferred from past bookings
            }
            
            # Calculate scores for all photographers
            photographer_scores = []
            for photographer in photographers:
                if photographer.get('is_active', False):
                    score = self.calculate_photographer_score(photographer, user_preferences, reviews)
                    photographer_scores.append((photographer, score))
            
            # Sort by score and return top recommendations
            photographer_scores.sort(key=lambda x: x[1], reverse=True)
            recommendations = [p[0] for p in photographer_scores[:limit]]
            
            return recommendations
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return []

@ai_bp.route('/api/recommendations')
def get_recommendations():
    """API endpoint for photographer recommendations"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    event_type = request.args.get('event_type')
    location = request.args.get('location')
    limit = int(request.args.get('limit', 10))
    
    engine = RecommendationEngine()
    recommendations = engine.get_recommendations(session['user_id'], event_type, location, limit)
    
    # Convert to JSON-serializable format
    recommendations_data = []
    for photographer in recommendations:
        recommendations_data.append({
            'photographer_id': photographer.get('photographer_id'),
            'name': photographer.get('name'),
            'specialization': photographer.get('specialization'),
            'location': photographer.get('location'),
            'rating': photographer.get('average_rating', 4.0),
            'price_range': photographer.get('price_range', 'medium')
        })
    
    return jsonify({'recommendations': recommendations_data})

# ---------------------------------------
# Intelligent Pricing System
# ---------------------------------------

class PricingEngine:
    def __init__(self):
        self.base_prices = {
            'wedding': 1500,
            'portrait': 300,
            'event': 800,
            'commercial': 1200,
            'family': 400
        }
        self.location_multipliers = {
            'mumbai': 1.5,
            'delhi': 1.4,
            'bangalore': 1.3,
            'hyderabad': 1.2,
            'chennai': 1.2,
            'pune': 1.1
        }
    
    def calculate_dynamic_price(self, event_type, location, date, duration, photographer_rating=4.0):
        """Calculate dynamic pricing based on various factors"""
        try:
            # Base price
            base_price = self.base_prices.get(event_type.lower(), 500)
            
            # Location multiplier
            location_multiplier = 1.0
            for city, multiplier in self.location_multipliers.items():
                if city in location.lower():
                    location_multiplier = multiplier
                    break
            
            # Date-based pricing (weekend premium, holiday premium)
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            date_multiplier = 1.0
            
            # Weekend premium
            if date_obj.weekday() >= 5:  # Saturday or Sunday
                date_multiplier += 0.2
            
            # Holiday season premium (December, May-June for weddings)
            if date_obj.month in [12, 5, 6]:
                date_multiplier += 0.15
            
            # Duration multiplier
            duration_multiplier = max(1.0, duration / 2.0)  # Base 2 hours
            
            # Photographer rating multiplier
            rating_multiplier = max(0.8, photographer_rating / 5.0)
            
            # Demand-based pricing (simplified)
            demand_multiplier = self.calculate_demand_multiplier(date, location)
            
            # Calculate final price
            final_price = (base_price * 
                          location_multiplier * 
                          date_multiplier * 
                          duration_multiplier * 
                          rating_multiplier * 
                          demand_multiplier)
            
            return {
                'base_price': base_price,
                'final_price': round(final_price, 2),
                'factors': {
                    'location_multiplier': location_multiplier,
                    'date_multiplier': date_multiplier,
                    'duration_multiplier': duration_multiplier,
                    'rating_multiplier': rating_multiplier,
                    'demand_multiplier': demand_multiplier
                }
            }
        except Exception as e:
            print(f"Error calculating price: {e}")
            return {'base_price': 500, 'final_price': 500, 'factors': {}}
    
    def calculate_demand_multiplier(self, date, location):
        """Calculate demand multiplier based on historical data"""
        try:
            # Get bookings for similar dates and locations
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            start_date = (date_obj - timedelta(days=30)).isoformat()
            end_date = (date_obj + timedelta(days=30)).isoformat()
            
            # This would query actual booking data in a real implementation
            # For now, we'll simulate demand based on date patterns
            
            # Higher demand on weekends
            if date_obj.weekday() >= 5:
                return 1.2
            
            # Higher demand in wedding season
            if date_obj.month in [11, 12, 1, 2, 5, 6]:
                return 1.15
            
            return 1.0
        except:
            return 1.0

@ai_bp.route('/api/pricing')
def get_pricing():
    """API endpoint for dynamic pricing"""
    event_type = request.args.get('event_type', 'portrait')
    location = request.args.get('location', 'hyderabad')
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    duration = float(request.args.get('duration', 2))
    photographer_rating = float(request.args.get('rating', 4.0))
    
    engine = PricingEngine()
    pricing = engine.calculate_dynamic_price(event_type, location, date, duration, photographer_rating)
    
    return jsonify(pricing)

# ---------------------------------------
# Intelligent Scheduling System
# ---------------------------------------

class SchedulingEngine:
    def __init__(self):
        self.time_slots = [
            '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', 
            '15:00', '16:00', '17:00', '18:00', '19:00', '20:00'
        ]
    
    def find_optimal_slots(self, photographer_id, date, duration):
        """Find optimal time slots for booking"""
        try:
            # Get existing bookings for the photographer on the date
            existing_bookings = bookings_table.query(
                IndexName='PhotographerIndex',
                KeyConditionExpression='photographer_id = :photographer_id AND event_date = :date',
                ExpressionAttributeValues={
                    ':photographer_id': photographer_id,
                    ':date': date
                }
            )
            
            booked_slots = []
            for booking in existing_bookings.get('Items', []):
                if booking.get('booking_status') in ['confirmed', 'pending']:
                    start_time = booking.get('event_time')
                    booking_duration = int(booking.get('duration', 2))
                    booked_slots.append((start_time, booking_duration))
            
            # Find available slots
            available_slots = []
            for slot in self.time_slots:
                if self.is_slot_available(slot, duration, booked_slots):
                    # Calculate slot score based on various factors
                    score = self.calculate_slot_score(slot, date, duration)
                    available_slots.append({
                        'time': slot,
                        'score': score,
                        'recommended': score > 0.7
                    })
            
            # Sort by score
            available_slots.sort(key=lambda x: x['score'], reverse=True)
            return available_slots
            
        except Exception as e:
            print(f"Error finding optimal slots: {e}")
            return []
    
    def is_slot_available(self, start_time, duration, booked_slots):
        """Check if a time slot is available"""
        start_hour = int(start_time.split(':')[0])
        end_hour = start_hour + duration
        
        for booked_start, booked_duration in booked_slots:
            booked_start_hour = int(booked_start.split(':')[0])
            booked_end_hour = booked_start_hour + booked_duration
            
            # Check for overlap
            if not (end_hour <= booked_start_hour or start_hour >= booked_end_hour):
                return False
        
        return True
    
    def calculate_slot_score(self, time_slot, date, duration):
        """Calculate score for a time slot"""
        hour = int(time_slot.split(':')[0])
        score = 0.5  # Base score
        
        # Golden hour preference for outdoor shoots
        if hour in [16, 17, 18]:  # 4-6 PM
            score += 0.3
        
        # Morning preference for events
        if hour in [10, 11, 12]:  # 10 AM - 12 PM
            score += 0.2
        
        # Avoid very early or very late slots
        if hour < 9 or hour > 19:
            score -= 0.2
        
        # Weekend preference
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        if date_obj.weekday() >= 5:
            score += 0.1
        
        return min(1.0, max(0.0, score))

@ai_bp.route('/api/optimal-slots')
def get_optimal_slots():
    """API endpoint for optimal time slots"""
    photographer_id = request.args.get('photographer_id')
    date = request.args.get('date')
    duration = int(request.args.get('duration', 2))
    
    if not photographer_id or not date:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    engine = SchedulingEngine()
    slots = engine.find_optimal_slots(photographer_id, date, duration)
    
    return jsonify({'available_slots': slots})

# ---------------------------------------
# Sentiment Analysis and Insights
# ---------------------------------------

@ai_bp.route('/api/sentiment-insights')
def get_sentiment_insights():
    """Get advanced sentiment insights from reviews and feedback"""
    try:
        # Get all reviews
        reviews_response = reviews_table.scan()
        reviews = reviews_response.get('Items', [])
        
        # Analyze sentiment trends
        sentiment_trends = defaultdict(list)
        topic_sentiments = defaultdict(list)
        
        for review in reviews:
            created_date = review.get('created_at', '')[:10]  # Get date part
            sentiment = review.get('sentiment', 'neutral')
            sentiment_score = float(review.get('sentiment_score', 0))
            
            sentiment_trends[created_date].append(sentiment_score)
            
            # Extract topics using simple keyword matching
            review_text = review.get('review_text', '').lower()
            topics = extract_topics(review_text)
            for topic in topics:
                topic_sentiments[topic].append(sentiment_score)
        
        # Calculate averages
        trend_data = {}
        for date, scores in sentiment_trends.items():
            trend_data[date] = sum(scores) / len(scores) if scores else 0
        
        topic_data = {}
        for topic, scores in topic_sentiments.items():
            topic_data[topic] = {
                'average_sentiment': sum(scores) / len(scores) if scores else 0,
                'review_count': len(scores)
            }
        
        return jsonify({
            'sentiment_trends': trend_data,
            'topic_sentiments': topic_data,
            'total_reviews': len(reviews)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def extract_topics(text):
    """Extract topics from review text using keyword matching"""
    topics = []
    keywords = {
        'communication': ['communication', 'responsive', 'contact', 'reply'],
        'quality': ['quality', 'professional', 'skill', 'talent'],
        'punctuality': ['time', 'punctual', 'late', 'early', 'schedule'],
        'pricing': ['price', 'cost', 'expensive', 'affordable', 'value'],
        'creativity': ['creative', 'artistic', 'unique', 'innovative']
    }
    
    for topic, words in keywords.items():
        if any(word in text for word in words):
            topics.append(topic)
    
    return topics if topics else ['general']
