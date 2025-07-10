# Task Manager - DevOps Learning Project

A production-ready Flask web application designed for DevOps training and deployment practice. This app includes both a web interface and REST API, making it perfect for learning containerization, CI/CD, cloud deployment, and monitoring.

## 🎯 Learning Objectives

By working with this project, you'll gain hands-on experience with:
- **Application Deployment**: From local development to production
- **Containerization**: Docker, orchestration, and microservices
- **CI/CD Pipelines**: Automated testing and deployment
- **Infrastructure as Code**: Terraform, CloudFormation
- **Cloud Platforms**: AWS, Azure, GCP deployment strategies
- **Monitoring & Logging**: Application observability
- **Database Management**: PostgreSQL in production environments

## Application Features

- **Dashboard**: Real-time task statistics and visualizations
- **Task Management**: Full CRUD operations with filtering and pagination
- **User Management**: User registration, authentication, and profiles
- **REST API**: Complete API endpoints for all operations
- **Database**: PostgreSQL with proper relationships and migrations
- **Health Checks**: Built-in monitoring endpoints
- **Logging**: Comprehensive logging with rotation
- **Modern UI**: Responsive Bootstrap design with interactive features

## Prerequisites

### For Local Development
- Windows 10/11, macOS, or Linux
- Python 3.8+
- PostgreSQL (or SQLite for testing)
- Internet connection

### For Complete DevOps Labs
- **AWS Account** with appropriate permissions (free tier sufficient)
- **GitHub Account** for CI/CD integration
- **Administrator/sudo access** for tool installations
- **Basic command line** knowledge
- **6-8 hours** to complete all labs

### Tools Installed in Lab 01
- AWS CLI
- Terraform
- Docker Desktop
- Git

## 🚀 Getting Started

### Option 1: Quick Local Development
**Perfect for testing the application quickly**

### Option 2: Complete DevOps Learning Path
**For production-ready deployment and DevOps skills**

📚 **[Begin Lab Series →](./Instructions/README.md)**

*The labs build upon the local setup, so complete the local development setup first.*

---

## 🚀 Quick Start Guide

### Production-Ready Setup (PostgreSQL)

**For students learning production deployments**

#### 1. Install Prerequisites
```bash
# Install Python 3.8+ (check "Add to PATH" during installation)
python --version  # Verify installation

# Install PostgreSQL
# Download from postgresql.org and remember your postgres password
psql --version  # Verify installation
```

#### 2. Set Up Database
```bash
# Connect to PostgreSQL as admin
psql -U postgres

# Create database and user
CREATE DATABASE taskmanager;
CREATE USER taskuser WITH PASSWORD 'taskpass';
GRANT ALL PRIVILEGES ON DATABASE taskmanager TO taskuser;
GRANT CREATE ON SCHEMA public TO taskuser;
GRANT USAGE ON SCHEMA public TO taskuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO taskuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO taskuser;
\q
```

#### 3. Set Up Application
```bash
# Clone the repository
git clone https://github.com/Jagjeet-Dhuna/task-manager-devops.git
cd task-manager-devops

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set up environment (copy .env.example to .env)
cp .env.example .env

# Initialize database with sample data
python init_db.py --sample-data

# Run the application
python app.py
```

**✅ Success!** Visit **http://localhost:5000**

---

### Option 2: Quick Start (SQLite)

**For rapid testing and development**

```bash
# Set up application (same as above)
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Configure for SQLite in .env file
DATABASE_URL=sqlite:///taskmanager.db

# Initialize and run
python init_db.py --sample-data
python app.py
```

**✅ Success!** Visit **http://localhost:5000**

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

## 🎓 DevOps Lab Series Overview

This project includes comprehensive hands-on labs that teach modern DevOps practices:

| Lab | Focus Area | Duration | Skills Learned |
|-----|------------|----------|----------------|
| [01](./Instructions/01-environment-setup-containerization.md) | Environment Setup | 60 min | AWS CLI, Terraform, Docker, Git |
| [02](./Instructions/02-infrastructure-foundation-terraform.md) | Infrastructure Foundation | 90 min | VPC, Security Groups, Terraform Modules |
| [03](./Instructions/03-database-infrastructure-management.md) | Database Management | 45 min | RDS, Backup, Monitoring |
| [04](./Instructions/04-compute-infrastructure-load-balancing.md) | Compute & Load Balancing | 75 min | EC2, Auto Scaling, ALB |
| [05](./Instructions/05-cicd-pipeline-implementation.md) | CI/CD Pipeline | 90 min | GitHub Actions, Testing, Security |
| [06](./Instructions/06-monitoring-logging-alerting.md) | Monitoring & Alerting | 60 min | CloudWatch, Dashboards, Alerts |
| [07](./Instructions/07-multi-environment-deployment-management.md) | Multi-Environment | 45 min | Staging, Production, DR |

**Total Time: 6-8 hours** | **Skill Level: Beginner to Intermediate**

## 📚 DevOps Learning Path

Once you have the application running locally, progress through these comprehensive labs:

### 🎓 Complete Lab Series (6-8 hours total)
Follow the detailed lab instructions in the `Instructions/` folder:

**Phase 1: Foundation (2.5 hours)**
- **Lab 01**: Environment Setup and Application Containerization (60 min)
- **Lab 02**: Infrastructure Foundation with Terraform (90 min)

**Phase 2: Infrastructure (2 hours)**  
- **Lab 03**: Database Infrastructure and Management (45 min)
- **Lab 04**: Compute Infrastructure and Load Balancing (75 min)

**Phase 3: Automation (2.5 hours)**
- **Lab 05**: CI/CD Pipeline Implementation (90 min)
- **Lab 06**: Monitoring, Logging, and Alerting (60 min)

**Phase 4: Production Management (45 min)**
- **Lab 07**: Multi-Environment Deployment and Management (45 min)

📖 **[Start with Lab 01: Environment Setup](./Instructions/01-environment-setup-containerization.md)**

## 🤝 Contributing

This is an educational project. Feel free to:
- Fork and modify for your learning needs
- Submit issues for bugs or improvements
- Create pull requests for enhancements
- Share your deployment experiences
