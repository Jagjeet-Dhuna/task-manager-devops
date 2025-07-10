from flask import Blueprint, request, jsonify, current_app
from models import db, User, Task, TaskStatus, TaskPriority
from datetime import datetime
import re

api = Blueprint('api', __name__)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_user_data(data, required_fields=None):
    if required_fields is None:
        required_fields = ['username', 'email']
    
    errors = []
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f'{field} is required')
    
    if 'email' in data and data['email'] and not validate_email(data['email']):
        errors.append('Invalid email format')
    
    if 'username' in data and data['username'] and len(data['username']) < 3:
        errors.append('Username must be at least 3 characters')
    
    return errors

def validate_task_data(data, required_fields=None):
    if required_fields is None:
        required_fields = ['title', 'user_id']
    
    errors = []
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f'{field} is required')
    
    if 'title' in data and data['title'] and len(data['title']) < 1:
        errors.append('Title cannot be empty')
    
    if 'status' in data and data['status']:
        valid_statuses = [status.value for status in TaskStatus]
        if data['status'] not in valid_statuses:
            errors.append(f'Status must be one of: {", ".join(valid_statuses)}')
    
    if 'priority' in data and data['priority']:
        valid_priorities = [priority.value for priority in TaskPriority]
        if data['priority'] not in valid_priorities:
            errors.append(f'Priority must be one of: {", ".join(valid_priorities)}')
    
    return errors

# User endpoints
@api.route('/users', methods=['GET'])
def get_users():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        
        users = User.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': users.total,
                'pages': users.pages
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f'Error fetching users: {str(e)}')
        return jsonify({'error': 'Failed to fetch users'}), 500

@api.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        return jsonify(user.to_dict()), 200
    except Exception as e:
        current_app.logger.error(f'Error fetching user {user_id}: {str(e)}')
        return jsonify({'error': 'User not found'}), 404

@api.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        errors = validate_user_data(data, ['username', 'email', 'password'])
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 409
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 409
        
        user = User(
            username=data['username'],
            email=data['email']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        current_app.logger.info(f'User created: {user.username}')
        return jsonify(user.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating user: {str(e)}')
        return jsonify({'error': 'Failed to create user'}), 500

@api.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        errors = validate_user_data(data, [])
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        if 'username' in data and data['username'] != user.username:
            if User.query.filter_by(username=data['username']).first():
                return jsonify({'error': 'Username already exists'}), 409
            user.username = data['username']
        
        if 'email' in data and data['email'] != user.email:
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'error': 'Email already exists'}), 409
            user.email = data['email']
        
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        if 'is_active' in data:
            user.is_active = bool(data['is_active'])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        current_app.logger.info(f'User updated: {user.username}')
        return jsonify(user.to_dict()), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating user {user_id}: {str(e)}')
        return jsonify({'error': 'Failed to update user'}), 500

@api.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        username = user.username
        
        db.session.delete(user)
        db.session.commit()
        
        current_app.logger.info(f'User deleted: {username}')
        return jsonify({'message': 'User deleted successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting user {user_id}: {str(e)}')
        return jsonify({'error': 'Failed to delete user'}), 500

# Task endpoints
@api.route('/tasks', methods=['GET'])
def get_tasks():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        user_id = request.args.get('user_id', type=int)
        status = request.args.get('status')
        priority = request.args.get('priority')
        
        query = Task.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if status:
            try:
                status_enum = TaskStatus(status)
                query = query.filter_by(status=status_enum)
            except ValueError:
                return jsonify({'error': f'Invalid status: {status}'}), 400
        
        if priority:
            try:
                priority_enum = TaskPriority(priority)
                query = query.filter_by(priority=priority_enum)
            except ValueError:
                return jsonify({'error': f'Invalid priority: {priority}'}), 400
        
        tasks = query.order_by(Task.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'tasks': [task.to_dict() for task in tasks.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': tasks.total,
                'pages': tasks.pages
            }
        }), 200
    
    except Exception as e:
        current_app.logger.error(f'Error fetching tasks: {str(e)}')
        return jsonify({'error': 'Failed to fetch tasks'}), 500

@api.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    try:
        task = Task.query.get_or_404(task_id)
        return jsonify(task.to_dict()), 200
    except Exception as e:
        current_app.logger.error(f'Error fetching task {task_id}: {str(e)}')
        return jsonify({'error': 'Task not found'}), 404

@api.route('/tasks', methods=['POST'])
def create_task():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        errors = validate_task_data(data, ['title', 'user_id'])
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        task = Task(
            title=data['title'],
            description=data.get('description', ''),
            user_id=data['user_id']
        )
        
        if 'status' in data:
            task.status = TaskStatus(data['status'])
        
        if 'priority' in data:
            task.priority = TaskPriority(data['priority'])
        
        if 'due_date' in data and data['due_date']:
            try:
                task.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid due_date format. Use ISO format.'}), 400
        
        db.session.add(task)
        db.session.commit()
        
        current_app.logger.info(f'Task created: {task.title} for user {user.username}')
        return jsonify(task.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error creating task: {str(e)}')
        return jsonify({'error': 'Failed to create task'}), 500

@api.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    try:
        task = Task.query.get_or_404(task_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        errors = validate_task_data(data, [])
        if errors:
            return jsonify({'error': 'Validation failed', 'details': errors}), 400
        
        if 'title' in data:
            task.title = data['title']
        
        if 'description' in data:
            task.description = data['description']
        
        if 'status' in data:
            old_status = task.status
            task.status = TaskStatus(data['status'])
            
            if old_status != TaskStatus.COMPLETED and task.status == TaskStatus.COMPLETED:
                task.completed_at = datetime.utcnow()
            elif old_status == TaskStatus.COMPLETED and task.status != TaskStatus.COMPLETED:
                task.completed_at = None
        
        if 'priority' in data:
            task.priority = TaskPriority(data['priority'])
        
        if 'due_date' in data:
            if data['due_date']:
                try:
                    task.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
                except ValueError:
                    return jsonify({'error': 'Invalid due_date format. Use ISO format.'}), 400
            else:
                task.due_date = None
        
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        current_app.logger.info(f'Task updated: {task.title}')
        return jsonify(task.to_dict()), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating task {task_id}: {str(e)}')
        return jsonify({'error': 'Failed to update task'}), 500

@api.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        task = Task.query.get_or_404(task_id)
        task_title = task.title
        
        db.session.delete(task)
        db.session.commit()
        
        current_app.logger.info(f'Task deleted: {task_title}')
        return jsonify({'message': 'Task deleted successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting task {task_id}: {str(e)}')
        return jsonify({'error': 'Failed to delete task'}), 500

@api.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    try:
        user = User.query.get_or_404(user_id)
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        status = request.args.get('status')
        priority = request.args.get('priority')
        
        query = Task.query.filter_by(user_id=user_id)
        
        if status:
            try:
                status_enum = TaskStatus(status)
                query = query.filter_by(status=status_enum)
            except ValueError:
                return jsonify({'error': f'Invalid status: {status}'}), 400
        
        if priority:
            try:
                priority_enum = TaskPriority(priority)
                query = query.filter_by(priority=priority_enum)
            except ValueError:
                return jsonify({'error': f'Invalid priority: {priority}'}), 400
        
        tasks = query.order_by(Task.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'user': user.to_dict(),
            'tasks': [task.to_dict() for task in tasks.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': tasks.total,
                'pages': tasks.pages
            }
        }), 200
    
    except Exception as e:
        current_app.logger.error(f'Error fetching tasks for user {user_id}: {str(e)}')
        return jsonify({'error': 'Failed to fetch user tasks'}), 500

@api.route('/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    try:
        stats = {
            'total_users': User.query.count(),
            'total_tasks': Task.query.count(),
            'pending_tasks': Task.query.filter_by(status=TaskStatus.PENDING).count(),
            'in_progress_tasks': Task.query.filter_by(status=TaskStatus.IN_PROGRESS).count(),
            'completed_tasks': Task.query.filter_by(status=TaskStatus.COMPLETED).count(),
        }
        return jsonify(stats), 200
    except Exception as e:
        current_app.logger.error(f'Error fetching dashboard stats: {str(e)}')
        return jsonify({'error': 'Failed to fetch dashboard stats'}), 500