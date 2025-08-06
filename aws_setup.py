import boto3
import json
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS Configuration
AWS_REGION_NAME = os.environ.get('AWS_REGION_NAME', 'ap-south-1')

# Initialize AWS clients
dynamodb = boto3.client('dynamodb', region_name=AWS_REGION_NAME)
sns = boto3.client('sns', region_name=AWS_REGION_NAME)

def create_users_table():
    """Create Users table in DynamoDB"""
    table_name = 'CaptureMomentsUsers'
    
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'email',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'email',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserIdIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'user_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"✅ Created table: {table_name}")
        return response
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️  Table {table_name} already exists")
        else:
            print(f"❌ Error creating table {table_name}: {e}")
        return None

def create_photographers_table():
    """Create Photographers table in DynamoDB"""
    table_name = 'CaptureMomentsPhotographers'
    
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'photographer_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'photographer_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'specialization',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'location',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'SpecializationIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'specialization',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                },
                {
                    'IndexName': 'LocationIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'location',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"✅ Created table: {table_name}")
        return response
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️  Table {table_name} already exists")
        else:
            print(f"❌ Error creating table {table_name}: {e}")
        return None

def create_bookings_table():
    """Create Bookings table in DynamoDB"""
    table_name = 'CaptureMomentsBookings'
    
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'booking_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'booking_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'photographer_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'event_date',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'user_id',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'event_date',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                },
                {
                    'IndexName': 'PhotographerIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'photographer_id',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'event_date',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"✅ Created table: {table_name}")
        return response
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️  Table {table_name} already exists")
        else:
            print(f"❌ Error creating table {table_name}: {e}")
        return None

def create_feedback_table():
    """Create Feedback table in DynamoDB"""
    table_name = 'CaptureMomentsFeedback'
    
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'feedback_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'feedback_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'user_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'created_at',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'user_id',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'created_at',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'BillingMode': 'PAY_PER_REQUEST'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"✅ Created table: {table_name}")
        return response
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️  Table {table_name} already exists")
        else:
            print(f"❌ Error creating table {table_name}: {e}")
        return None

def create_sns_topic():
    """Create SNS topic for notifications"""
    topic_name = 'CaptureMomentsAlerts'
    
    try:
        response = sns.create_topic(Name=topic_name)
        topic_arn = response['TopicArn']
        print(f"✅ Created SNS topic: {topic_name}")
        print(f"📧 Topic ARN: {topic_arn}")
        return topic_arn
    except ClientError as e:
        print(f"❌ Error creating SNS topic: {e}")
        return None

def setup_aws_resources():
    """Setup all AWS resources for Capture Moments"""
    print("🚀 Setting up AWS resources for Capture Moments...")
    print("=" * 50)
    
    # Create DynamoDB tables
    create_users_table()
    create_photographers_table()
    create_bookings_table()
    create_feedback_table()
    
    # Create SNS topic
    topic_arn = create_sns_topic()
    
    print("=" * 50)
    print("✅ AWS setup completed!")
    
    if topic_arn:
        print(f"\n📝 Update your .env file with:")
        print(f"SNS_TOPIC_ARN={topic_arn}")
        print(f"ENABLE_SNS=True")

if __name__ == "__main__":
    setup_aws_resources()
