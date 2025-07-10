# Task Manager Web Application

A production-ready Flask web application for task management with both web interface and REST API, built for DevOps deployment practice.

## Features

- **Web Interface**: Complete web application with dashboard, task management, and user management
- **REST API Endpoints**: Complete CRUD operations for users and tasks
- **Database Integration**: PostgreSQL with SQLAlchemy ORM
- **Environment Configuration**: Support for dev/staging/prod environments
- **Health Monitoring**: Health check endpoint for load balancers
- **Logging**: Comprehensive logging with rotation
- **Input Validation**: Proper request validation and error handling
- **Relationship Management**: User-Task relationships with foreign keys
- **Modern UI**: Bootstrap-based responsive design with interactive features

## Prerequisites

Before starting, ensure you have:
- Windows 10/11 (or Linux/macOS)
- Python 3.8+
- PostgreSQL (or SQLite for testing)
- Administrator privileges (for PostgreSQL installation)
- Internet connection

## Quick Start

### Option 1: Full Setup with PostgreSQL (Recommended for Production-like Environment)

#### Step 1: Install Python

1. Download Python 3.8+ from [python.org](https://www.python.org/downloads/)
2. During installation, **check "Add Python to PATH"**
3. Verify installation:
```cmd
python --version
pip --version
```

#### Step 2: Install PostgreSQL

1. Download PostgreSQL from [postgresql.org](https://www.postgresql.org/download/windows/)
2. Run the installer and remember the password you set for the `postgres` user
3. Add PostgreSQL to PATH (usually `C:\Program Files\PostgreSQL\15\bin`)
4. Verify installation:
```cmd
psql --version
```

#### Step 3: Create Database

1. Open Command Prompt as Administrator
2. Connect to PostgreSQL:
```cmd
psql -U postgres
```
3. Create database and user:
```sql
CREATE DATABASE taskmanager;
CREATE USER taskuser WITH PASSWORD 'taskpass';
GRANT ALL PRIVILEGES ON DATABASE taskmanager TO taskuser;
GRANT CREATE ON SCHEMA public TO taskuser;
GRANT USAGE ON SCHEMA public TO taskuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO taskuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO taskuser;
\q
```

#### Step 4: Set up Python Environment

1. Clone or download the project
2. Open Command Prompt in your project directory
3. Create virtual environment:
```cmd
python -m venv venv
```
4. Activate virtual environment:
```cmd
venv\Scripts\activate
```
5. Install dependencies:
```cmd
pip install -r requirements.txt
```

#### Step 5: Configure Environment

1. Copy the environment template:
```cmd
copy .env.example .env
```
2. Edit `.env` file (optional - defaults should work):
```
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=your-secret-key-change-in-production
DATABASE_URL=postgresql://taskuser:taskpass@localhost/taskmanager
```

#### Step 6: Initialize Database

```cmd
python init_db.py --sample-data
```

#### Step 7: Run the Application

```cmd
python app.py
```

**Success!** Open your browser and go to: **http://localhost:5000**

---

### Option 2: Quick Setup with SQLite (Easier for Testing)

If PostgreSQL setup seems complex, here's a simpler SQLite option:

#### Step 1: Install Python (same as above)

#### Step 2: Set up Python Environment

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

#### Step 3: Configure for SQLite

Edit your `.env` file:
```
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=your-secret-key-change-in-production
DATABASE_URL=sqlite:///taskmanager.db
```

#### Step 4: Initialize Database

```cmd
python init_db.py --sample-data
```

#### Step 5: Run the Application

```cmd
python app.py
```

**Success!** Open your browser and go to: **http://localhost:5000**

---

## Application Overview

### Web Interface
- **Dashboard**: `http://localhost:5000/` - View task statistics and recent tasks
- **Tasks**: `http://localhost:5000/tasks` - Manage all tasks
- **Users**: `http://localhost:5000/users` - Manage users
- **Health Check**: `http://localhost:5000/health` - System health status

### API Endpoints

#### Health Check
- `GET /health` - Service health status

#### Dashboard
- `GET /api/dashboard-stats` - Get dashboard statistics

#### Users
- `GET /api/users` - List all users (paginated)
- `GET /api/users/{id}` - Get specific user
- `POST /api/users` - Create new user
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user

#### Tasks
- `GET /api/tasks` - List all tasks (paginated, filterable)
- `GET /api/tasks/{id}` - Get specific task
- `POST /api/tasks` - Create new task
- `PUT /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task
- `GET /api/users/{id}/tasks` - Get tasks for specific user

## Database Schema

### Users Table
- `id` (Primary Key)
- `username` (Unique)
- `email` (Unique)
- `password_hash`
- `created_at`
- `updated_at`
- `is_active`

### Tasks Table
- `id` (Primary Key)
- `title`
- `description`
- `status` (pending, in_progress, completed)
- `priority` (low, medium, high)
- `due_date`
- `created_at`
- `updated_at`
- `completed_at`
- `user_id` (Foreign Key)

## Sample Data

The application comes with sample data including:

**Users:**
- alice_dev (alice@example.com)
- bob_manager (bob@example.com)
- charlie_tester (charlie@example.com)

**Password for all users:** `password123`

**Tasks:** Various tasks with different statuses and priorities

## Sample API Usage

### Create a User
```bash
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepassword"
  }'
```

### Create a Task
```bash
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Deploy application",
    "description": "Deploy the app to production",
    "priority": "high",
    "user_id": 1,
    "due_date": "2024-01-15T10:00:00Z"
  }'
```

### Get Tasks (with filters)
```bash
curl "http://localhost:5000/api/tasks?status=pending&priority=high&page=1&per_page=10"
```

### Health Check
```bash
curl http://localhost:5000/health
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `development` |
| `FLASK_DEBUG` | Debug mode | `false` |
| `SECRET_KEY` | Flask secret key | `dev-secret-key` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://taskuser:taskpass@localhost/taskmanager` |

## Troubleshooting

### PostgreSQL Connection Issues

**Error: "psql: error: connection to server at "localhost" (::1), port 5432 failed"**

**Solution:**
1. Make sure PostgreSQL service is running:
   - Open Services (`services.msc`)
   - Find "postgresql-x64-15" service
   - Right-click → Start

2. Check if PostgreSQL is listening:
```cmd
netstat -an | findstr :5432
```

### Python Path Issues

**Error: "'python' is not recognized as an internal or external command"**

**Solution:**
1. Reinstall Python with "Add to PATH" checked
2. Or manually add Python to PATH:
   - Windows Key + R → `sysdm.cpl` → Advanced → Environment Variables
   - Add Python installation directory to PATH

### Permission Issues

**Error: "Access denied" when installing packages**

**Solution:**
1. Run Command Prompt as Administrator
2. Or use `--user` flag:
```cmd
pip install --user -r requirements.txt
```

### Port Already in Use

**Error: "Address already in use"**

**Solution:**
1. Find process using port 5000:
```cmd
netstat -ano | findstr :5000
```
2. Kill the process:
```cmd
taskkill /PID <process_id> /F
```

### Database Permission Issues

**Error: "permission denied for database/schema"**

**Solution:**
1. Reconnect to PostgreSQL as postgres user:
```cmd
psql -U postgres
```
2. Re-grant permissions:
```sql
GRANT ALL PRIVILEGES ON DATABASE taskmanager TO taskuser;
GRANT CREATE ON SCHEMA public TO taskuser;
GRANT USAGE ON SCHEMA public TO taskuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO taskuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO taskuser;
```

### Enum Template Issues

**Error: "'models.TaskStatus object' has no attribute 'replace'"**

This has been fixed in the current version. The templates now properly use `.value` property for enum objects.

## Production Deployment

### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Environment Configuration
Set these environment variables for production:
```bash
export FLASK_ENV=production
export FLASK_DEBUG=false
export SECRET_KEY=your-secure-secret-key
export DATABASE_URL=postgresql://user:pass@host/db
```

### Docker Support
Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## Testing

### Web Interface Testing

1. **Dashboard** (http://localhost:5000/)
   - View task statistics
   - See recent tasks
   - Check system health

2. **Task Management** (http://localhost:5000/tasks)
   - Create new tasks
   - Edit existing tasks
   - Filter by status/priority
   - Delete tasks

3. **User Management** (http://localhost:5000/users)
   - Create new users
   - Edit user details
   - View user tasks
   - Delete users

### API Testing

Test the REST API endpoints using curl or Postman:

```cmd
# Health check
curl http://localhost:5000/health

# Get all users
curl http://localhost:5000/api/users

# Get all tasks
curl http://localhost:5000/api/tasks

# Create a new user
curl -X POST http://localhost:5000/api/users -H "Content-Type: application/json" -d "{\"username\":\"testuser\",\"email\":\"test@example.com\",\"password\":\"password123\"}"
```

## Logging

Logs are written to `logs/taskmanager.log` with rotation enabled. Log levels:
- INFO: Application startup, user/task operations
- ERROR: Database errors, validation failures
- WARNING: Authentication failures, rate limiting

## Error Handling

The API returns consistent JSON error responses:
```json
{
  "error": "Validation failed",
  "details": ["Username is required", "Email is required"]
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `409` - Conflict
- `500` - Internal Server Error

## Development Notes

- Database connection pooling is configured for production
- Input validation prevents SQL injection
- Passwords are hashed using Werkzeug
- Pagination is implemented for list endpoints
- Foreign key relationships maintain data integrity
- Proper logging for debugging and monitoring
- Bootstrap modals with error handling
- Chart.js integration for dashboard visualization
- Real-time dashboard updates every 30 seconds

## Stopping the Application

- **Command Prompt:** Press `Ctrl + C`
- **PowerShell:** Press `Ctrl + C`
- **Background Process:** Use Task Manager to end Python processes

## Next Steps for DevOps Training

Once running locally, you can:

1. **Containerize** with Docker
2. **Set up CI/CD** with GitHub Actions
3. **Deploy to cloud** (AWS, Azure, GCP)
4. **Configure monitoring** and logging
5. **Set up load balancing**
6. **Implement database migrations**

The application is designed to be production-ready and includes all the features you'd expect to deploy in a real enterprise environment!

## License

This project is created for DevOps practice and learning purposes.