from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, User, Task, TaskStatus, TaskPriority
from sqlalchemy import func

web = Blueprint('web', __name__)

@web.route('/')
def index():
    # Get statistics for dashboard
    stats = {
        'total_users': User.query.count(),
        'total_tasks': Task.query.count(),
        'pending_tasks': Task.query.filter_by(status=TaskStatus.PENDING).count(),
        'in_progress_tasks': Task.query.filter_by(status=TaskStatus.IN_PROGRESS).count(),
        'completed_tasks': Task.query.filter_by(status=TaskStatus.COMPLETED).count(),
    }
    
    # Get recent tasks
    recent_tasks = Task.query.order_by(Task.created_at.desc()).limit(10).all()
    
    return render_template('index.html', stats=stats, recent_tasks=recent_tasks)

@web.route('/tasks')
def tasks():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Build query with filters
    query = Task.query
    
    # Filter by status
    status = request.args.get('status')
    if status:
        try:
            status_enum = TaskStatus(status)
            query = query.filter_by(status=status_enum)
        except ValueError:
            flash('Invalid status filter', 'error')
    
    # Filter by priority
    priority = request.args.get('priority')
    if priority:
        try:
            priority_enum = TaskPriority(priority)
            query = query.filter_by(priority=priority_enum)
        except ValueError:
            flash('Invalid priority filter', 'error')
    
    # Filter by user
    user_id = request.args.get('user_id', type=int)
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    # Execute query with pagination
    tasks_pagination = query.order_by(Task.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get all users for the dropdown
    users = User.query.filter_by(is_active=True).order_by(User.username).all()
    
    return render_template('tasks.html', 
                         tasks=tasks_pagination.items, 
                         pagination=tasks_pagination,
                         users=users)

@web.route('/users')
def users():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get users with pagination
    users_pagination = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get statistics
    active_users = User.query.filter_by(is_active=True).count()
    total_tasks = Task.query.count()
    
    return render_template('users.html', 
                         users=users_pagination.items, 
                         pagination=users_pagination,
                         active_users=active_users,
                         total_tasks=total_tasks)

@web.route('/user/<int:user_id>/tasks')
def user_tasks(user_id):
    user = User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get user's tasks with pagination
    tasks_pagination = Task.query.filter_by(user_id=user_id).order_by(Task.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('user_tasks.html',
                         user=user,
                         tasks=tasks_pagination.items,
                         pagination=tasks_pagination)

@web.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@web.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500