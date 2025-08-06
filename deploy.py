#!/usr/bin/env python3
"""
Deployment Script for Capture Moments
Automates AWS infrastructure setup and application deployment
"""

import boto3
import json
import time
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CaptureMonentsDeployer:
    def __init__(self):
        self.region = os.environ.get('AWS_REGION_NAME', 'ap-south-1')
        self.ec2 = boto3.client('ec2', region_name=self.region)
        self.dynamodb = boto3.client('dynamodb', region_name=self.region)
        self.sns = boto3.client('sns', region_name=self.region)
        self.s3 = boto3.client('s3', region_name=self.region)
        self.iam = boto3.client('iam', region_name=self.region)
        
        self.app_name = 'capture-moments'
        self.bucket_name = f'{self.app_name}-{int(time.time())}'
        
    def create_s3_bucket(self):
        """Create S3 bucket for file storage"""
        try:
            if self.region == 'us-east-1':
                self.s3.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            
            # Configure bucket for web access
            self.s3.put_bucket_cors(
                Bucket=self.bucket_name,
                CORSConfiguration={
                    'CORSRules': [{
                        'AllowedHeaders': ['*'],
                        'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE'],
                        'AllowedOrigins': ['*'],
                        'MaxAgeSeconds': 3000
                    }]
                }
            )
            
            print(f"✅ Created S3 bucket: {self.bucket_name}")
            return self.bucket_name
            
        except ClientError as e:
            print(f"❌ Error creating S3 bucket: {e}")
            return None
    
    def create_dynamodb_tables(self):
        """Create all required DynamoDB tables"""
        tables = [
            {
                'TableName': 'CaptureMomentsUsers',
                'KeySchema': [{'AttributeName': 'email', 'KeyType': 'HASH'}],
                'AttributeDefinitions': [
                    {'AttributeName': 'email', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                'GlobalSecondaryIndexes': [{
                    'IndexName': 'UserIdIndex',
                    'KeySchema': [{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
                    'Projection': {'ProjectionType': 'ALL'},
                    'BillingMode': 'PAY_PER_REQUEST'
                }]
            },
            {
                'TableName': 'CaptureMomentsPhotographers',
                'KeySchema': [{'AttributeName': 'photographer_id', 'KeyType': 'HASH'}],
                'AttributeDefinitions': [
                    {'AttributeName': 'photographer_id', 'AttributeType': 'S'},
                    {'AttributeName': 'specialization', 'AttributeType': 'S'},
                    {'AttributeName': 'location', 'AttributeType': 'S'}
                ],
                'GlobalSecondaryIndexes': [
                    {
                        'IndexName': 'SpecializationIndex',
                        'KeySchema': [{'AttributeName': 'specialization', 'KeyType': 'HASH'}],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    },
                    {
                        'IndexName': 'LocationIndex',
                        'KeySchema': [{'AttributeName': 'location', 'KeyType': 'HASH'}],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ]
            },
            {
                'TableName': 'CaptureMomentsBookings',
                'KeySchema': [{'AttributeName': 'booking_id', 'KeyType': 'HASH'}],
                'AttributeDefinitions': [
                    {'AttributeName': 'booking_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'photographer_id', 'AttributeType': 'S'},
                    {'AttributeName': 'event_date', 'AttributeType': 'S'}
                ],
                'GlobalSecondaryIndexes': [
                    {
                        'IndexName': 'UserIndex',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'event_date', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    },
                    {
                        'IndexName': 'PhotographerIndex',
                        'KeySchema': [
                            {'AttributeName': 'photographer_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'event_date', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ]
            },
            {
                'TableName': 'CaptureMomentsFeedback',
                'KeySchema': [{'AttributeName': 'feedback_id', 'KeyType': 'HASH'}],
                'AttributeDefinitions': [
                    {'AttributeName': 'feedback_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'created_at', 'AttributeType': 'S'}
                ],
                'GlobalSecondaryIndexes': [{
                    'IndexName': 'UserIndex',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'BillingMode': 'PAY_PER_REQUEST'
                }]
            },
            # Advanced feature tables
            {
                'TableName': 'CaptureMomentsReviews',
                'KeySchema': [{'AttributeName': 'review_id', 'KeyType': 'HASH'}],
                'AttributeDefinitions': [
                    {'AttributeName': 'review_id', 'AttributeType': 'S'},
                    {'AttributeName': 'photographer_id', 'AttributeType': 'S'},
                    {'AttributeName': 'created_at', 'AttributeType': 'S'}
                ],
                'GlobalSecondaryIndexes': [{
                    'IndexName': 'PhotographerIndex',
                    'KeySchema': [
                        {'AttributeName': 'photographer_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'BillingMode': 'PAY_PER_REQUEST'
                }]
            },
            {
                'TableName': 'CaptureMomentsGalleries',
                'KeySchema': [{'AttributeName': 'gallery_id', 'KeyType': 'HASH'}],
                'AttributeDefinitions': [
                    {'AttributeName': 'gallery_id', 'AttributeType': 'S'},
                    {'AttributeName': 'photographer_id', 'AttributeType': 'S'},
                    {'AttributeName': 'upload_date', 'AttributeType': 'S'}
                ],
                'GlobalSecondaryIndexes': [{
                    'IndexName': 'PhotographerIndex',
                    'KeySchema': [
                        {'AttributeName': 'photographer_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'upload_date', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'BillingMode': 'PAY_PER_REQUEST'
                }]
            },
            {
                'TableName': 'CaptureMomentsMessages',
                'KeySchema': [{'AttributeName': 'message_id', 'KeyType': 'HASH'}],
                'AttributeDefinitions': [
                    {'AttributeName': 'message_id', 'AttributeType': 'S'},
                    {'AttributeName': 'room_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                ],
                'GlobalSecondaryIndexes': [{
                    'IndexName': 'RoomIndex',
                    'KeySchema': [
                        {'AttributeName': 'room_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'BillingMode': 'PAY_PER_REQUEST'
                }]
            },
            {
                'TableName': 'CaptureMonentsChatRooms',
                'KeySchema': [{'AttributeName': 'room_id', 'KeyType': 'HASH'}],
                'AttributeDefinitions': [
                    {'AttributeName': 'room_id', 'AttributeType': 'S'}
                ]
            },
            {
                'TableName': 'CaptureMomentsPayments',
                'KeySchema': [{'AttributeName': 'payment_id', 'KeyType': 'HASH'}],
                'AttributeDefinitions': [
                    {'AttributeName': 'payment_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'created_at', 'AttributeType': 'S'}
                ],
                'GlobalSecondaryIndexes': [{
                    'IndexName': 'UserIndex',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'BillingMode': 'PAY_PER_REQUEST'
                }]
            }
        ]
        
        created_tables = []
        for table_config in tables:
            try:
                # Set billing mode for all tables
                table_config['BillingMode'] = 'PAY_PER_REQUEST'
                
                # Create table
                response = self.dynamodb.create_table(**table_config)
                created_tables.append(table_config['TableName'])
                print(f"✅ Created table: {table_config['TableName']}")
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceInUseException':
                    print(f"⚠️  Table {table_config['TableName']} already exists")
                else:
                    print(f"❌ Error creating table {table_config['TableName']}: {e}")
        
        return created_tables
    
    def create_sns_topic(self):
        """Create SNS topic for notifications"""
        try:
            response = self.sns.create_topic(Name='CaptureMomentsAlerts')
            topic_arn = response['TopicArn']
            print(f"✅ Created SNS topic: {topic_arn}")
            return topic_arn
        except ClientError as e:
            print(f"❌ Error creating SNS topic: {e}")
            return None
    
    def create_ec2_instance(self):
        """Create EC2 instance for hosting the application"""
        try:
            # Create security group
            sg_response = self.ec2.create_security_group(
                GroupName=f'{self.app_name}-sg',
                Description='Security group for Capture Moments application'
            )
            security_group_id = sg_response['GroupId']
            
            # Add inbound rules
            self.ec2.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 80,
                        'ToPort': 80,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 443,
                        'ToPort': 443,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    },
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 5000,
                        'ToPort': 5000,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            )
            
            # Launch EC2 instance
            user_data_script = """#!/bin/bash
            yum update -y
            yum install -y python3 python3-pip git
            pip3 install --upgrade pip
            
            # Clone application (replace with your repository)
            cd /home/ec2-user
            # git clone https://github.com/your-repo/capture-moments.git
            
            # Install dependencies
            # cd capture-moments
            # pip3 install -r requirements.txt
            
            # Start application
            # python3 app.py
            """
            
            response = self.ec2.run_instances(
                ImageId='ami-0c02fb55956c7d316',  # Amazon Linux 2 AMI
                MinCount=1,
                MaxCount=1,
                InstanceType='t2.micro',
                SecurityGroupIds=[security_group_id],
                UserData=user_data_script,
                TagSpecifications=[{
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'Name', 'Value': f'{self.app_name}-server'},
                        {'Key': 'Project', 'Value': 'CaptureMonents'}
                    ]
                }]
            )
            
            instance_id = response['Instances'][0]['InstanceId']
            print(f"✅ Created EC2 instance: {instance_id}")
            return instance_id
            
        except ClientError as e:
            print(f"❌ Error creating EC2 instance: {e}")
            return None
    
    def deploy_all(self):
        """Deploy complete infrastructure"""
        print("🚀 Starting Capture Moments deployment...")
        print("=" * 60)
        
        # Create S3 bucket
        bucket_name = self.create_s3_bucket()
        
        # Create DynamoDB tables
        tables = self.create_dynamodb_tables()
        
        # Create SNS topic
        topic_arn = self.create_sns_topic()
        
        # Create EC2 instance
        instance_id = self.create_ec2_instance()
        
        print("=" * 60)
        print("✅ Deployment completed!")
        print("\n📝 Configuration Summary:")
        print(f"S3 Bucket: {bucket_name}")
        print(f"SNS Topic ARN: {topic_arn}")
        print(f"EC2 Instance ID: {instance_id}")
        print(f"DynamoDB Tables: {len(tables)} created")
        
        print("\n🔧 Update your .env file with:")
        print(f"S3_BUCKET_NAME={bucket_name}")
        print(f"SNS_TOPIC_ARN={topic_arn}")
        print("ENABLE_SNS=True")
        
        return {
            'bucket_name': bucket_name,
            'topic_arn': topic_arn,
            'instance_id': instance_id,
            'tables': tables
        }

if __name__ == "__main__":
    deployer = CaptureMonentsDeployer()
    deployer.deploy_all()
