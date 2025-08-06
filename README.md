# Capture Moments - AWS Powered Photographer Booking System

A comprehensive cloud-based photographer booking platform built with Flask and AWS services, designed to connect clients with professional photographers for weddings, events, portraits, and commercial photography.

## 🚀 Features

### Core Features
- **User Authentication**: Secure registration and login for clients, photographers, and admins
- **Role-Based Access Control**: Different dashboards and permissions for each user type
- **Photographer Profiles**: Detailed profiles with specializations, portfolios, and availability
- **Booking System**: Real-time booking with availability checking and conflict resolution
- **AWS Integration**: Built on AWS EC2, DynamoDB, and SNS for scalability and reliability
- **Sentiment Analysis**: Automatic feedback sentiment analysis using TextBlob
- **Email Notifications**: Automated email alerts for bookings and updates
- **Responsive Design**: Mobile-friendly interface with Bootstrap 5

### Advanced Features
- **Real-time Chat System**: WebSocket-based messaging between clients and photographers
- **AI-Powered Recommendations**: Smart photographer suggestions based on user preferences
- **Dynamic Pricing**: Intelligent pricing based on demand, location, and photographer ratings
- **Photo Gallery System**: Portfolio management with S3 storage and categorization
- **Review & Rating System**: Comprehensive review system with sentiment analysis
- **Payment Integration**: Stripe payment processing with booking confirmation
- **File Sharing**: Secure file upload and sharing in chat rooms
- **Intelligent Scheduling**: AI-powered optimal time slot recommendations
- **Advanced Analytics**: Sentiment trends, booking patterns, and performance insights
- **Real-time Notifications**: Live updates for bookings, messages, and system events

### AI & Machine Learning Features
- **Smart Photographer Matching**: ML-based recommendation engine
- **Automated Pricing Optimization**: Dynamic pricing based on multiple factors
- **Sentiment Analysis**: Advanced text analysis for reviews and feedback
- **Demand Prediction**: Intelligent forecasting for peak booking periods
- **Optimal Scheduling**: AI-powered time slot optimization
- **Topic Extraction**: Automatic categorization of feedback topics

## 🛠 Technology Stack

### Backend Technologies
- **Framework**: Flask (Python) with SocketIO for real-time features
- **Database**: AWS DynamoDB with optimized GSI indexes
- **Cloud Platform**: AWS (EC2, DynamoDB, SNS, S3, Comprehend)
- **Authentication**: Werkzeug Security with JWT tokens
- **Real-time Communication**: WebSocket with Socket.IO
- **Task Queue**: Celery with Redis for background processing
- **Caching**: Redis for session management and caching

### Frontend Technologies
- **UI Framework**: Bootstrap 5 with custom CSS
- **JavaScript**: Vanilla JS with Socket.IO client
- **Real-time Features**: WebSocket connections for chat and notifications
- **File Upload**: Drag-and-drop with progress indicators
- **Charts & Analytics**: Chart.js for data visualization

### AI & Machine Learning
- **Sentiment Analysis**: TextBlob and AWS Comprehend
- **Recommendation Engine**: Custom collaborative filtering
- **Pricing Algorithm**: Multi-factor dynamic pricing model
- **Scheduling Optimization**: Time slot optimization algorithms

### Payment & Integration
- **Payment Processing**: Stripe API integration
- **Email Service**: SMTP with HTML templates
- **File Storage**: AWS S3 with CDN distribution
- **Notifications**: AWS SNS for multi-channel alerts

## 📋 Prerequisites

### Hardware Requirements
- **Processor**: Intel i5 or equivalent (minimum)
- **RAM**: 4 GB (8 GB recommended for Full Stack development)
- **Storage**: 128 GB SSD or HDD
- **Internet**: High-speed internet (minimum 10 Mbps)

### Software Requirements
- **Python**: 3.8 or higher
- **Web Browser**: Google Chrome, Firefox, or Microsoft Edge (updated)
- **IDE**: Visual Studio Code (recommended)
- **Git**: Latest version
- **AWS Account**: For cloud services

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd "Capture Moments"
```

### 2. Create Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and update with your AWS credentials:
```bash
cp .env.example .env
```

Edit `.env` file:
```env
# AWS Configuration
AWS_REGION_NAME=ap-south-1
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# Email Configuration (Optional)
ENABLE_EMAIL=True
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password

# SNS Configuration (Optional)
ENABLE_SNS=True
SNS_TOPIC_ARN=your_sns_topic_arn
```

### 5. Setup AWS Resources
```bash
python aws_setup.py
```

### 6. Run the Application
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## 📊 Database Schema

### Users Table
- **Primary Key**: email
- **Attributes**: user_id, username, password, role, created_at, is_active

### Photographers Table
- **Primary Key**: photographer_id
- **Attributes**: name, email, specialization, location, bio, portfolio, pricing, is_active
- **GSI**: SpecializationIndex, LocationIndex

### Bookings Table
- **Primary Key**: booking_id
- **Attributes**: user_id, photographer_id, event_date, event_time, event_type, location, status
- **GSI**: UserIndex, PhotographerIndex

### Feedback Table
- **Primary Key**: feedback_id
- **Attributes**: user_id, feedback_type, subject, message, sentiment, sentiment_score, status

## 🎯 Usage Scenarios

### Scenario 1: Efficient Booking System for Clients
Clients can easily log in, browse available photographers, check their specializations and availability, and book sessions for their preferred dates. The AWS EC2 infrastructure ensures reliable performance even during peak booking periods.

### Scenario 2: Centralized Booking Management
All booking requests are processed through Flask and stored in DynamoDB, providing a centralized system for managing photographer schedules, client preferences, and booking history.

### Scenario 3: Easy Access to Photography Services
The platform provides seamless access to photography services with real-time availability checking, instant booking confirmations, and automated notifications powered by AWS SNS.

## 🔧 API Endpoints

### Authentication & User Management
- `POST /register` - User registration with role selection
- `POST /login` - User login with session management
- `GET /logout` - User logout and session cleanup
- `GET /profile` - User profile management
- `PUT /profile` - Update user profile

### Photographer Management
- `GET /photographers` - List photographers with filters
- `GET /photographer/<id>` - Detailed photographer profile
- `POST /photographer/profile` - Create/update photographer profile
- `GET /advanced/gallery/<photographer_id>` - Photographer's photo gallery
- `POST /advanced/upload-photos/<photographer_id>` - Upload portfolio photos

### Booking System
- `POST /book/<photographer_id>` - Create new booking request
- `GET /my-bookings` - User's booking history
- `PUT /booking/<booking_id>/status` - Update booking status
- `GET /photographer/bookings` - Photographer's bookings
- `POST /advanced/add-review/<booking_id>` - Add booking review

### AI-Powered Features
- `GET /ai/api/recommendations` - Get personalized photographer recommendations
- `GET /ai/api/pricing` - Dynamic pricing calculation
- `GET /ai/api/optimal-slots` - Optimal time slot suggestions
- `GET /ai/api/sentiment-insights` - Advanced sentiment analysis

### Real-time Chat System
- `GET /chat/<booking_id>` - Access chat room for booking
- `POST /chat/upload-file/<room_id>` - Upload file to chat
- `GET /chat/api/chat/rooms` - Get user's chat rooms
- `GET /chat/api/chat/messages/<room_id>` - Get chat messages
- **WebSocket Events**: `connect`, `join_room`, `send_message`, `typing`

### Payment Integration
- `GET /advanced/payment/<booking_id>` - Payment page
- `POST /advanced/process-payment` - Process Stripe payment
- `GET /payment/history` - Payment transaction history

### Analytics & Admin
- `GET /admin/dashboard` - Comprehensive admin dashboard
- `GET /api/sentiment-stats` - Sentiment analysis statistics
- `GET /api/recent-feedback` - Recent customer feedback
- `GET /admin/users` - User management interface
- `GET /admin/bookings` - All bookings management

## 🚀 Deployment

### AWS EC2 Deployment
1. Launch an EC2 instance (t2.micro for testing, t2.small+ for production)
2. Install Python, pip, and required dependencies
3. Clone the repository and configure environment variables
4. Setup DynamoDB tables using `aws_setup.py`
5. Configure security groups for HTTP/HTTPS access
6. Use a process manager like Gunicorn for production

### Environment Setup
```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 🔒 Security Features

- **Password Hashing**: Werkzeug security for password protection
- **Session Management**: Secure session handling
- **Input Validation**: Form validation and sanitization
- **AWS IAM**: Proper IAM roles and permissions
- **Environment Variables**: Sensitive data stored in environment variables

## 📈 Monitoring & Analytics

- **Booking Analytics**: Track booking trends and patterns
- **Sentiment Analysis**: Monitor customer satisfaction through feedback
- **Performance Metrics**: AWS CloudWatch integration for system monitoring
- **Error Tracking**: Comprehensive error logging and handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and questions:
- **Email**: support@capturemoments.com
- **Phone**: +91 9876543210
- **Location**: Hyderabad, India

## 🙏 Acknowledgments

- AWS for cloud infrastructure
- Flask community for the excellent framework
- Bootstrap team for responsive design components
- TextBlob for sentiment analysis capabilities
