#!/usr/bin/env python3
"""
Database initialization script for Task Manager API
Creates tables and optionally populates with sample data
"""

import os
import sys
from datetime import datetime, timedelta
from flask import Flask
from models import db, User, Task, TaskStatus, TaskPriority
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def init_database(app, with_sample_data=False):
    """Initialize database tables and optionally add sample data"""
    with app.app_context():
        # Drop all tables if they exist
        db.drop_all()
        print("Dropped existing tables")
        
        # Create all tables
        db.create_all()
        print("Created database tables")
        
        if with_sample_data:
            populate_sample_data()
            print("Added sample data")

def populate_sample_data():
    """Add sample users and tasks for testing"""
    # Create sample users
    users_data = [
        {
            'username': 'alice_dev',
            'email': 'alice@example.com',
            'password': 'password123'
        },
        {
            'username': 'bob_manager',
            'email': 'bob@example.com',
            'password': 'password123'
        },
        {
            'username': 'charlie_tester',
            'email': 'charlie@example.com',
            'password': 'password123'
        }
    ]
    
    users = []
    for user_data in users_data:
        user = User(
            username=user_data['username'],
            email=user_data['email']
        )
        user.set_password(user_data['password'])
        db.session.add(user)
        users.append(user)
    
    db.session.flush()  # Flush to get user IDs
    
    # Create sample tasks
    tasks_data = [
        {
            'title': 'Set up CI/CD pipeline',
            'description': 'Configure GitHub Actions for automated testing and deployment',
            'status': TaskStatus.IN_PROGRESS,
            'priority': TaskPriority.HIGH,
            'user_id': users[0].id,
            'due_date': datetime.utcnow() + timedelta(days=3)
        },
        {
            'title': 'Write API documentation',
            'description': 'Create comprehensive API documentation using OpenAPI/Swagger',
            'status': TaskStatus.PENDING,
            'priority': TaskPriority.MEDIUM,
            'user_id': users[0].id,
            'due_date': datetime.utcnow() + timedelta(days=7)
        },
        {
            'title': 'Review code changes',
            'description': 'Review pull requests for the authentication module',
            'status': TaskStatus.COMPLETED,
            'priority': TaskPriority.HIGH,
            'user_id': users[1].id,
            'completed_at': datetime.utcnow() - timedelta(days=1)
        },
        {
            'title': 'Deploy staging environment',
            'description': 'Set up staging environment on AWS ECS',
            'status': TaskStatus.PENDING,
            'priority': TaskPriority.HIGH,
            'user_id': users[1].id,
            'due_date': datetime.utcnow() + timedelta(days=2)
        },
        {
            'title': 'Write unit tests',
            'description': 'Increase test coverage for user authentication endpoints',
            'status': TaskStatus.IN_PROGRESS,
            'priority': TaskPriority.MEDIUM,
            'user_id': users[2].id,
            'due_date': datetime.utcnow() + timedelta(days=5)
        },
        {
            'title': 'Performance testing',
            'description': 'Load test the API endpoints with various scenarios',
            'status': TaskStatus.PENDING,
            'priority': TaskPriority.LOW,
            'user_id': users[2].id,
            'due_date': datetime.utcnow() + timedelta(days=10)
        },
        {
            'title': 'Database migration',
            'description': 'Migrate user data from legacy system',
            'status': TaskStatus.COMPLETED,
            'priority': TaskPriority.HIGH,
            'user_id': users[1].id,
            'completed_at': datetime.utcnow() - timedelta(days=3)
        },
        {
            'title': 'Security audit',
            'description': 'Conduct security review of authentication and authorization',
            'status': TaskStatus.PENDING,
            'priority': TaskPriority.HIGH,
            'user_id': users[0].id,
            'due_date': datetime.utcnow() + timedelta(days=14)
        }
    ]
    
    for task_data in tasks_data:
        task = Task(
            title=task_data['title'],
            description=task_data['description'],
            status=task_data['status'],
            priority=task_data['priority'],
            user_id=task_data['user_id']
        )
        if 'due_date' in task_data:
            task.due_date = task_data['due_date']
        if 'completed_at' in task_data:
            task.completed_at = task_data['completed_at']
        
        db.session.add(task)
    
    db.session.commit()
    print(f"Created {len(users)} users and {len(tasks_data)} tasks")

def main():
    """Main function to run database initialization"""
    app = create_app()
    
    # Check if sample data should be added
    with_sample_data = '--sample-data' in sys.argv or '-s' in sys.argv
    
    try:
        init_database(app, with_sample_data)
        print("Database initialization completed successfully!")
        
        if with_sample_data:
            print("\nSample users created:")
            print("- alice_dev (alice@example.com)")
            print("- bob_manager (bob@example.com)")
            print("- charlie_tester (charlie@example.com)")
            print("Password for all users: password123")
            print("\nSample tasks created with various statuses and priorities")
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()