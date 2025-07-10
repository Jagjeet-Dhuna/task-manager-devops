# Lab 05: CI/CD Pipeline Implementation

## Overview

In this lab, you will implement a comprehensive CI/CD pipeline using GitHub Actions. You'll create automated testing, security scanning, Docker image building, and multi-environment deployment workflows. The pipeline will integrate with your existing AWS infrastructure to enable continuous delivery.

## Objectives

After completing this lab, you will be able to:
- Create GitHub Actions workflows for automated testing and building
- Implement security scanning and code quality checks
- Set up automated Docker image building and ECR deployment
- Configure multi-environment deployment pipelines
- Implement deployment approval workflows and rollback procedures

## Prerequisites

- Completed Lab 04 (Compute Infrastructure and Load Balancing)
- Understanding of CI/CD concepts and Git workflows
- Basic knowledge of GitHub Actions
- Existing AWS infrastructure and ECR repository

## Duration

**Estimated Time:** 90 minutes

---

## Exercise 1: Set up GitHub Actions Workflow Structure

### Task 1: Create Workflow Directory Structure

1. **Create GitHub Actions workflow directories:**
   ```bash
   mkdir -p .github/workflows
   mkdir -p .github/scripts
   mkdir -p tests/unit
   mkdir -p tests/integration
   ```

2. **Create workflow configuration file:**
   ```yaml
   # .github/workflows/ci-cd.yml
   name: CI/CD Pipeline
   
   on:
     push:
       branches: [ main, develop ]
     pull_request:
       branches: [ main, develop ]
     workflow_dispatch:
       inputs:
         environment:
           description: 'Environment to deploy to'
           required: true
           default: 'dev'
           type: choice
           options:
             - dev
             - staging
             - prod
   
   env:
     AWS_REGION: us-east-1
     ECR_REPOSITORY: ${{ secrets.ECR_REPOSITORY }}
     PROJECT_NAME: taskmanager
   
   jobs:
     # Job definitions will be added in subsequent tasks
   ```

### Task 2: Create GitHub Secrets

1. **Create required secrets in GitHub repository:**
   ```bash
   # Navigate to GitHub repository → Settings → Secrets and variables → Actions
   # Add the following secrets:
   ```

   **Required Secrets:**
   - `AWS_ACCESS_KEY_ID` - AWS access key for CI/CD
   - `AWS_SECRET_ACCESS_KEY` - AWS secret key for CI/CD
   - `ECR_REPOSITORY` - ECR repository URL
   - `DB_PASSWORD` - Database password for testing
   - `SECRET_KEY` - Flask secret key
   - `SLACK_WEBHOOK_URL` - (Optional) Slack webhook for notifications

2. **Create environment-specific secrets:**
   ```bash
   # For each environment (dev, staging, prod):
   # DEV_DB_ENDPOINT - Database endpoint for dev
   # STAGING_DB_ENDPOINT - Database endpoint for staging
   # PROD_DB_ENDPOINT - Database endpoint for prod
   ```

### Task 3: Create Test Configuration

1. **Create `pytest.ini` configuration:**
   ```ini
   [tool:pytest]
   testpaths = tests
   python_files = test_*.py
   python_classes = Test*
   python_functions = test_*
   addopts = 
       --verbose
       --tb=short
       --strict-markers
       --cov=app
       --cov-report=term-missing
       --cov-report=html:htmlcov
       --cov-report=xml:coverage.xml
   markers =
       unit: Unit tests
       integration: Integration tests
       slow: Slow running tests
   ```

2. **Create `requirements-test.txt`:**
   ```txt
   pytest==7.4.3
   pytest-cov==4.1.0
   pytest-mock==3.11.1
   pytest-flask==1.3.0
   pytest-postgresql==5.0.0
   requests==2.31.0
   coverage==7.3.2
   black==23.9.1
   flake8==6.1.0
   bandit==1.7.5
   safety==2.3.5
   ```

### ✅ Verification

1. **Check workflow structure:**
   ```bash
   tree .github/
   ```

2. **Validate workflow syntax:**
   ```bash
   # Use GitHub CLI to validate
   gh workflow list
   ```

---

## Exercise 2: Create Automated Testing and Security Scanning

### Task 1: Create Unit Tests

1. **Create `tests/unit/test_app.py`:**
   ```python
   import pytest
   from unittest.mock import patch, MagicMock
   import sys
   import os
   
   # Add the project root to the path
   sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
   
   from app import create_app
   
   @pytest.fixture
   def app():
       """Create and configure a test application."""
       app = create_app()
       app.config['TESTING'] = True
       app.config['WTF_CSRF_ENABLED'] = False
       app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
       
       with app.app_context():
           from models import db
           db.create_all()
           yield app
           db.drop_all()
   
   @pytest.fixture
   def client(app):
       """Create a test client."""
       return app.test_client()
   
   def test_health_endpoint(client):
       """Test health check endpoint."""
       response = client.get('/health')
       assert response.status_code == 200
       
       data = response.get_json()
       assert data['status'] == 'healthy'
       assert 'timestamp' in data
   
   def test_index_page(client):
       """Test index page loads."""
       response = client.get('/')
       assert response.status_code == 200
       assert b'Task Manager' in response.data
   
   def test_api_users_endpoint(client):
       """Test users API endpoint."""
       response = client.get('/api/users')
       assert response.status_code == 200
       
       data = response.get_json()
       assert 'users' in data
       assert isinstance(data['users'], list)
   
   def test_api_tasks_endpoint(client):
       """Test tasks API endpoint."""
       response = client.get('/api/tasks')
       assert response.status_code == 200
       
       data = response.get_json()
       assert 'tasks' in data
       assert isinstance(data['tasks'], list)
   
   def test_api_dashboard_stats(client):
       """Test dashboard stats endpoint."""
       response = client.get('/api/dashboard-stats')
       assert response.status_code == 200
       
       data = response.get_json()
       assert 'total_users' in data
       assert 'total_tasks' in data
       assert 'completed_tasks' in data
   
   @patch('models.User.query')
   def test_create_user(mock_query, client):
       """Test user creation."""
       mock_query.filter_by.return_value.first.return_value = None
       
       response = client.post('/api/users', json={
           'username': 'testuser',
           'email': 'test@example.com',
           'password': 'testpass123'
       })
       
       assert response.status_code == 201
   
   @patch('models.Task.query')
   def test_create_task(mock_query, client):
       """Test task creation."""
       response = client.post('/api/tasks', json={
           'title': 'Test Task',
           'description': 'Test Description',
           'priority': 'medium',
           'user_id': 1
       })
       
       assert response.status_code == 201
   ```

2. **Create `tests/unit/test_models.py`:**
   ```python
   import pytest
   from datetime import datetime
   import sys
   import os
   
   sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
   
   from models import User, Task, TaskStatus, TaskPriority
   
   def test_user_model():
       """Test User model."""
       user = User(
           username='testuser',
           email='test@example.com',
           password_hash='hashed_password'
       )
       
       assert user.username == 'testuser'
       assert user.email == 'test@example.com'
       assert user.password_hash == 'hashed_password'
   
   def test_task_model():
       """Test Task model."""
       task = Task(
           title='Test Task',
           description='Test Description',
           status=TaskStatus.PENDING,
           priority=TaskPriority.MEDIUM,
           user_id=1
       )
       
       assert task.title == 'Test Task'
       assert task.description == 'Test Description'
       assert task.status == TaskStatus.PENDING
       assert task.priority == TaskPriority.MEDIUM
       assert task.user_id == 1
   
   def test_task_status_enum():
       """Test TaskStatus enum."""
       assert TaskStatus.PENDING.value == 'pending'
       assert TaskStatus.IN_PROGRESS.value == 'in_progress'
       assert TaskStatus.COMPLETED.value == 'completed'
   
   def test_task_priority_enum():
       """Test TaskPriority enum."""
       assert TaskPriority.LOW.value == 'low'
       assert TaskPriority.MEDIUM.value == 'medium'
       assert TaskPriority.HIGH.value == 'high'
   ```

### Task 2: Create Integration Tests

1. **Create `tests/integration/test_database.py`:**
   ```python
   import pytest
   import os
   import sys
   import psycopg2
   from unittest.mock import patch
   
   sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
   
   from app import create_app
   from models import db, User, Task, TaskStatus, TaskPriority
   
   @pytest.fixture(scope='module')
   def app():
       """Create application for integration tests."""
       app = create_app()
       app.config['TESTING'] = True
       app.config['WTF_CSRF_ENABLED'] = False
       
       # Use test database
       test_db_url = os.environ.get('TEST_DATABASE_URL', 'postgresql://taskuser:taskpass@localhost:5432/taskmanager_test')
       app.config['SQLALCHEMY_DATABASE_URI'] = test_db_url
       
       with app.app_context():
           db.create_all()
           yield app
           db.drop_all()
   
   @pytest.fixture
   def client(app):
       """Create test client."""
       return app.test_client()
   
   @pytest.fixture
   def sample_user(app):
       """Create sample user."""
       with app.app_context():
           user = User(
               username='testuser',
               email='test@example.com',
               password_hash='hashed_password'
           )
           db.session.add(user)
           db.session.commit()
           return user
   
   @pytest.mark.integration
   def test_database_connection(app):
       """Test database connection."""
       with app.app_context():
           # Test database connection
           result = db.session.execute(db.text('SELECT 1'))
           assert result.scalar() == 1
   
   @pytest.mark.integration
   def test_user_crud_operations(app, client):
       """Test user CRUD operations."""
       with app.app_context():
           # Create user
           user = User(
               username='cruduser',
               email='crud@example.com',
               password_hash='hashed_password'
           )
           db.session.add(user)
           db.session.commit()
           
           # Read user
           found_user = User.query.filter_by(username='cruduser').first()
           assert found_user is not None
           assert found_user.email == 'crud@example.com'
           
           # Update user
           found_user.email = 'updated@example.com'
           db.session.commit()
           
           updated_user = User.query.filter_by(username='cruduser').first()
           assert updated_user.email == 'updated@example.com'
           
           # Delete user
           db.session.delete(found_user)
           db.session.commit()
           
           deleted_user = User.query.filter_by(username='cruduser').first()
           assert deleted_user is None
   
   @pytest.mark.integration
   def test_task_crud_operations(app, sample_user):
       """Test task CRUD operations."""
       with app.app_context():
           # Create task
           task = Task(
               title='Integration Test Task',
               description='Test Description',
               status=TaskStatus.PENDING,
               priority=TaskPriority.HIGH,
               user_id=sample_user.id
           )
           db.session.add(task)
           db.session.commit()
           
           # Read task
           found_task = Task.query.filter_by(title='Integration Test Task').first()
           assert found_task is not None
           assert found_task.description == 'Test Description'
           assert found_task.status == TaskStatus.PENDING
           
           # Update task
           found_task.status = TaskStatus.COMPLETED
           db.session.commit()
           
           updated_task = Task.query.filter_by(title='Integration Test Task').first()
           assert updated_task.status == TaskStatus.COMPLETED
           
           # Delete task
           db.session.delete(found_task)
           db.session.commit()
           
           deleted_task = Task.query.filter_by(title='Integration Test Task').first()
           assert deleted_task is None
   
   @pytest.mark.integration
   def test_user_task_relationship(app, sample_user):
       """Test user-task relationship."""
       with app.app_context():
           # Create tasks for user
           task1 = Task(
               title='Task 1',
               description='First task',
               status=TaskStatus.PENDING,
               priority=TaskPriority.LOW,
               user_id=sample_user.id
           )
           task2 = Task(
               title='Task 2',
               description='Second task',
               status=TaskStatus.IN_PROGRESS,
               priority=TaskPriority.MEDIUM,
               user_id=sample_user.id
           )
           
           db.session.add_all([task1, task2])
           db.session.commit()
           
           # Test relationship
           user_tasks = Task.query.filter_by(user_id=sample_user.id).all()
           assert len(user_tasks) == 2
           assert task1 in user_tasks
           assert task2 in user_tasks
   ```

### Task 3: Create Security and Quality Checks

1. **Create `.github/scripts/security-scan.sh`:**
   ```bash
   #!/bin/bash
   set -e
   
   echo "Running security scans..."
   
   # Run Bandit for security issues
   echo "Running Bandit security scan..."
   bandit -r app/ -f json -o bandit-report.json || true
   bandit -r app/ -f txt
   
   # Run Safety to check for known vulnerabilities
   echo "Running Safety check..."
   safety check --json --output safety-report.json || true
   safety check
   
   # Run Semgrep for additional security analysis
   if command -v semgrep &> /dev/null; then
       echo "Running Semgrep security scan..."
       semgrep --config=auto --json --output=semgrep-report.json app/ || true
       semgrep --config=auto app/
   fi
   
   echo "Security scans completed!"
   ```

2. **Create `.github/scripts/code-quality.sh`:**
   ```bash
   #!/bin/bash
   set -e
   
   echo "Running code quality checks..."
   
   # Run Black for code formatting
   echo "Checking code formatting with Black..."
   black --check --diff app/ tests/
   
   # Run flake8 for linting
   echo "Running flake8 linting..."
   flake8 app/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
   flake8 app/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
   
   # Run mypy for type checking (if type hints are used)
   if command -v mypy &> /dev/null; then
       echo "Running mypy type checking..."
       mypy app/ || true
   fi
   
   echo "Code quality checks completed!"
   ```

3. **Make scripts executable:**
   ```bash
   chmod +x .github/scripts/*.sh
   ```

### ✅ Verification

1. **Run unit tests locally:**
   ```bash
   python -m pytest tests/unit/ -v
   ```

2. **Run integration tests locally:**
   ```bash
   python -m pytest tests/integration/ -v -m integration
   ```

3. **Run security scans:**
   ```bash
   .github/scripts/security-scan.sh
   ```

---

## Exercise 3: Configure Docker Image Building and ECR Integration

### Task 1: Update CI/CD Workflow - Testing and Building

1. **Add testing jobs to `.github/workflows/ci-cd.yml`:**
   ```yaml
   jobs:
     test:
       runs-on: ubuntu-latest
       
       services:
         postgres:
           image: postgres:13
           env:
             POSTGRES_USER: taskuser
             POSTGRES_PASSWORD: taskpass
             POSTGRES_DB: taskmanager_test
           options: >-
             --health-cmd pg_isready
             --health-interval 10s
             --health-timeout 5s
             --health-retries 5
           ports:
             - 5432:5432
       
       steps:
         - name: Checkout code
           uses: actions/checkout@v4
         
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.9'
         
         - name: Cache pip dependencies
           uses: actions/cache@v3
           with:
             path: ~/.cache/pip
             key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
             restore-keys: |
               ${{ runner.os }}-pip-
         
         - name: Install dependencies
           run: |
             python -m pip install --upgrade pip
             pip install -r requirements.txt
             pip install -r requirements-test.txt
         
         - name: Run unit tests
           run: |
             python -m pytest tests/unit/ -v --cov=app --cov-report=xml
         
         - name: Run integration tests
           env:
             TEST_DATABASE_URL: postgresql://taskuser:taskpass@localhost:5432/taskmanager_test
           run: |
             python -m pytest tests/integration/ -v -m integration
         
         - name: Upload coverage reports
           uses: codecov/codecov-action@v3
           with:
             file: ./coverage.xml
             flags: unittests
             name: codecov-umbrella
   
     security-scan:
       runs-on: ubuntu-latest
       needs: test
       
       steps:
         - name: Checkout code
           uses: actions/checkout@v4
         
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.9'
         
         - name: Install security tools
           run: |
             python -m pip install --upgrade pip
             pip install bandit safety
         
         - name: Run security scans
           run: |
             .github/scripts/security-scan.sh
         
         - name: Upload security scan results
           uses: actions/upload-artifact@v3
           if: always()
           with:
             name: security-reports
             path: |
               bandit-report.json
               safety-report.json
   
     code-quality:
       runs-on: ubuntu-latest
       needs: test
       
       steps:
         - name: Checkout code
           uses: actions/checkout@v4
         
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.9'
         
         - name: Install code quality tools
           run: |
             python -m pip install --upgrade pip
             pip install black flake8
         
         - name: Run code quality checks
           run: |
             .github/scripts/code-quality.sh
   ```

### Task 2: Add Docker Build and Push Job

1. **Add build job to workflow:**
   ```yaml
   build:
     runs-on: ubuntu-latest
     needs: [test, security-scan, code-quality]
     if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'
     
     outputs:
       image-tag: ${{ steps.meta.outputs.tags }}
       image-digest: ${{ steps.build.outputs.digest }}
     
     steps:
       - name: Checkout code
         uses: actions/checkout@v4
       
       - name: Configure AWS credentials
         uses: aws-actions/configure-aws-credentials@v4
         with:
           aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
           aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
           aws-region: ${{ env.AWS_REGION }}
       
       - name: Login to Amazon ECR
         id: login-ecr
         uses: aws-actions/amazon-ecr-login@v2
       
       - name: Extract metadata
         id: meta
         uses: docker/metadata-action@v5
         with:
           images: ${{ secrets.ECR_REPOSITORY }}
           tags: |
             type=ref,event=branch
             type=ref,event=pr
             type=sha,prefix={{branch}}-
             type=raw,value=latest,enable={{is_default_branch}}
       
       - name: Set up Docker Buildx
         uses: docker/setup-buildx-action@v3
       
       - name: Build and push Docker image
         id: build
         uses: docker/build-push-action@v5
         with:
           context: .
           push: true
           tags: ${{ steps.meta.outputs.tags }}
           labels: ${{ steps.meta.outputs.labels }}
           cache-from: type=gha
           cache-to: type=gha,mode=max
           platforms: linux/amd64
       
       - name: Generate SBOM
         uses: anchore/sbom-action@v0
         with:
           image: ${{ secrets.ECR_REPOSITORY }}:${{ github.sha }}
           format: spdx-json
           output-file: sbom.spdx.json
       
       - name: Upload SBOM
         uses: actions/upload-artifact@v3
         with:
           name: sbom
           path: sbom.spdx.json
   ```

### Task 3: Create Container Security Scanning

1. **Add container security scan job:**
   ```yaml
   container-scan:
     runs-on: ubuntu-latest
     needs: build
     if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'
     
     steps:
       - name: Configure AWS credentials
         uses: aws-actions/configure-aws-credentials@v4
         with:
           aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
           aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
           aws-region: ${{ env.AWS_REGION }}
       
       - name: Login to Amazon ECR
         uses: aws-actions/amazon-ecr-login@v2
       
       - name: Scan image with Trivy
         uses: aquasecurity/trivy-action@master
         with:
           image-ref: ${{ secrets.ECR_REPOSITORY }}:${{ github.sha }}
           format: 'sarif'
           output: 'trivy-results.sarif'
       
       - name: Upload Trivy scan results to GitHub Security tab
         uses: github/codeql-action/upload-sarif@v2
         if: always()
         with:
           sarif_file: 'trivy-results.sarif'
       
       - name: Run Snyk to check Docker image for vulnerabilities
         uses: snyk/actions/docker@master
         env:
           SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
         with:
           image: ${{ secrets.ECR_REPOSITORY }}:${{ github.sha }}
           args: --severity-threshold=high --file=Dockerfile
         continue-on-error: true
   ```

### ✅ Verification

1. **Test Docker build locally:**
   ```bash
   docker build -t taskmanager:test .
   docker run --rm taskmanager:test python -c "print('Build successful')"
   ```

2. **Validate workflow syntax:**
   ```bash
   # Create a test push to trigger the workflow
   git add .github/workflows/ci-cd.yml
   git commit -m "Add CI/CD workflow"
   git push origin develop
   ```

---

## Exercise 4: Implement Multi-Environment Deployment Strategy

### Task 1: Create Environment-Specific Deployment Jobs

1. **Add deployment jobs to workflow:**
   ```yaml
   deploy-dev:
     runs-on: ubuntu-latest
     needs: [build, container-scan]
     if: github.ref == 'refs/heads/develop'
     environment: development
     
     steps:
       - name: Checkout code
         uses: actions/checkout@v4
       
       - name: Configure AWS credentials
         uses: aws-actions/configure-aws-credentials@v4
         with:
           aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
           aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
           aws-region: ${{ env.AWS_REGION }}
       
       - name: Deploy to development
         run: |
           .github/scripts/deploy.sh dev ${{ github.sha }}
       
       - name: Run smoke tests
         run: |
           .github/scripts/smoke-tests.sh dev
       
       - name: Notify deployment status
         if: always()
         uses: 8398a7/action-slack@v3
         with:
           status: ${{ job.status }}
           channel: '#deployments'
           webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
   
   deploy-staging:
     runs-on: ubuntu-latest
     needs: deploy-dev
     if: github.ref == 'refs/heads/main'
     environment: staging
     
     steps:
       - name: Checkout code
         uses: actions/checkout@v4
       
       - name: Configure AWS credentials
         uses: aws-actions/configure-aws-credentials@v4
         with:
           aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
           aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
           aws-region: ${{ env.AWS_REGION }}
       
       - name: Deploy to staging
         run: |
           .github/scripts/deploy.sh staging ${{ github.sha }}
       
       - name: Run integration tests
         run: |
           .github/scripts/integration-tests.sh staging
       
       - name: Notify deployment status
         if: always()
         uses: 8398a7/action-slack@v3
         with:
           status: ${{ job.status }}
           channel: '#deployments'
           webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
   
   deploy-production:
     runs-on: ubuntu-latest
     needs: deploy-staging
     if: github.ref == 'refs/heads/main'
     environment: production
     
     steps:
       - name: Checkout code
         uses: actions/checkout@v4
       
       - name: Configure AWS credentials
         uses: aws-actions/configure-aws-credentials@v4
         with:
           aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
           aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
           aws-region: ${{ env.AWS_REGION }}
       
       - name: Deploy to production
         run: |
           .github/scripts/deploy.sh prod ${{ github.sha }}
       
       - name: Run production smoke tests
         run: |
           .github/scripts/smoke-tests.sh prod
       
       - name: Notify deployment status
         if: always()
         uses: 8398a7/action-slack@v3
         with:
           status: ${{ job.status }}
           channel: '#deployments'
           webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
   ```

### Task 2: Create Deployment Scripts

1. **Create `.github/scripts/deploy.sh`:**
   ```bash
   #!/bin/bash
   set -e
   
   ENVIRONMENT=$1
   IMAGE_TAG=$2
   
   if [ -z "$ENVIRONMENT" ] || [ -z "$IMAGE_TAG" ]; then
       echo "Usage: $0 <environment> <image_tag>"
       exit 1
   fi
   
   echo "Deploying to $ENVIRONMENT environment with image tag $IMAGE_TAG"
   
   # Get Auto Scaling Group name
   ASG_NAME=$(aws autoscaling describe-auto-scaling-groups \
       --query "AutoScalingGroups[?contains(Tags[?Key=='Name'].Value, '$PROJECT_NAME-$ENVIRONMENT')].AutoScalingGroupName" \
       --output text)
   
   if [ -z "$ASG_NAME" ]; then
       echo "Error: Could not find Auto Scaling Group for $ENVIRONMENT"
       exit 1
   fi
   
   echo "Found Auto Scaling Group: $ASG_NAME"
   
   # Get current launch template
   LAUNCH_TEMPLATE_ID=$(aws autoscaling describe-auto-scaling-groups \
       --auto-scaling-group-names $ASG_NAME \
       --query 'AutoScalingGroups[0].LaunchTemplate.LaunchTemplateId' \
       --output text)
   
   echo "Current launch template: $LAUNCH_TEMPLATE_ID"
   
   # Create new launch template version with updated user data
   NEW_VERSION=$(aws ec2 create-launch-template-version \
       --launch-template-id $LAUNCH_TEMPLATE_ID \
       --source-version '$Latest' \
       --launch-template-data '{
           "UserData": "'$(echo "#!/bin/bash
   yum update -y
   yum install -y docker aws-cli jq
   
   service docker start
   usermod -a -G docker ec2-user
   
   # Login to ECR
   aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY
   
   # Pull and run new image
   docker pull $ECR_REPOSITORY:$IMAGE_TAG
   docker stop taskmanager || true
   docker rm taskmanager || true
   docker run -d \\
     --name taskmanager \\
     --restart unless-stopped \\
     -p 5000:5000 \\
     -e FLASK_ENV=production \\
     -e DATABASE_URL=\$(aws secretsmanager get-secret-value --secret-id taskmanager-$ENVIRONMENT-db-password --query SecretString --output text | jq -r '.password') \\
     $ECR_REPOSITORY:$IMAGE_TAG
   " | base64 -w 0)'"
       }' \
       --query 'LaunchTemplateVersion.VersionNumber' \
       --output text)
   
   echo "Created new launch template version: $NEW_VERSION"
   
   # Update Auto Scaling Group to use new launch template version
   aws autoscaling update-auto-scaling-group \
       --auto-scaling-group-name $ASG_NAME \
       --launch-template LaunchTemplateId=$LAUNCH_TEMPLATE_ID,Version=$NEW_VERSION
   
   echo "Updated Auto Scaling Group to use new launch template version"
   
   # Start instance refresh
   INSTANCE_REFRESH_ID=$(aws autoscaling start-instance-refresh \
       --auto-scaling-group-name $ASG_NAME \
       --preferences MinHealthyPercentage=50,InstanceWarmup=300 \
       --query 'InstanceRefreshId' \
       --output text)
   
   echo "Started instance refresh: $INSTANCE_REFRESH_ID"
   
   # Wait for instance refresh to complete
   echo "Waiting for instance refresh to complete..."
   while true; do
       STATUS=$(aws autoscaling describe-instance-refreshes \
           --auto-scaling-group-name $ASG_NAME \
           --instance-refresh-ids $INSTANCE_REFRESH_ID \
           --query 'InstanceRefreshes[0].Status' \
           --output text)
       
       echo "Instance refresh status: $STATUS"
       
       if [ "$STATUS" = "Successful" ]; then
           echo "Instance refresh completed successfully"
           break
       elif [ "$STATUS" = "Failed" ] || [ "$STATUS" = "Cancelled" ]; then
           echo "Instance refresh failed"
           exit 1
       fi
       
       sleep 30
   done
   
   echo "Deployment to $ENVIRONMENT completed successfully"
   ```

2. **Create `.github/scripts/smoke-tests.sh`:**
   ```bash
   #!/bin/bash
   set -e
   
   ENVIRONMENT=$1
   
   if [ -z "$ENVIRONMENT" ]; then
       echo "Usage: $0 <environment>"
       exit 1
   fi
   
   echo "Running smoke tests for $ENVIRONMENT environment"
   
   # Get ALB DNS name
   ALB_DNS=$(aws elbv2 describe-load-balancers \
       --query "LoadBalancers[?contains(LoadBalancerName, '$PROJECT_NAME-$ENVIRONMENT')].DNSName" \
       --output text)
   
   if [ -z "$ALB_DNS" ]; then
       echo "Error: Could not find ALB for $ENVIRONMENT"
       exit 1
   fi
   
   BASE_URL="http://$ALB_DNS"
   echo "Testing application at: $BASE_URL"
   
   # Test health endpoint
   echo "Testing health endpoint..."
   if curl -f -s "$BASE_URL/health" | jq -e '.status == "healthy"'; then
       echo "✅ Health check passed"
   else
       echo "❌ Health check failed"
       exit 1
   fi
   
   # Test main page
   echo "Testing main page..."
   if curl -f -s "$BASE_URL/" | grep -q "Task Manager"; then
       echo "✅ Main page accessible"
   else
       echo "❌ Main page test failed"
       exit 1
   fi
   
   # Test API endpoints
   echo "Testing API endpoints..."
   if curl -f -s "$BASE_URL/api/users" | jq -e '.users'; then
       echo "✅ Users API accessible"
   else
       echo "❌ Users API test failed"
       exit 1
   fi
   
   if curl -f -s "$BASE_URL/api/tasks" | jq -e '.tasks'; then
       echo "✅ Tasks API accessible"
   else
       echo "❌ Tasks API test failed"
       exit 1
   fi
   
   if curl -f -s "$BASE_URL/api/dashboard-stats" | jq -e '.total_users'; then
       echo "✅ Dashboard stats API accessible"
   else
       echo "❌ Dashboard stats API test failed"
       exit 1
   fi
   
   echo "All smoke tests passed for $ENVIRONMENT environment"
   ```

3. **Make scripts executable:**
   ```bash
   chmod +x .github/scripts/deploy.sh
   chmod +x .github/scripts/smoke-tests.sh
   ```

### ✅ Verification

1. **Test deployment script locally:**
   ```bash
   # Test with dry run
   .github/scripts/deploy.sh dev test-tag
   ```

2. **Test smoke tests:**
   ```bash
   .github/scripts/smoke-tests.sh dev
   ```

---

## Exercise 5: Test Complete CI/CD Pipeline

### Task 1: Create GitHub Environments

1. **Create environments in GitHub:**
   ```bash
   # Go to GitHub repository → Settings → Environments
   # Create environments: development, staging, production
   # Configure protection rules for staging and production
   ```

2. **Configure environment protection rules:**
   ```yaml
   # For staging and production environments:
   # - Required reviewers: 1
   # - Prevent administrators from bypassing
   # - Restrict deployments to protected branches
   ```

### Task 2: Create Rollback Workflow

1. **Create `.github/workflows/rollback.yml`:**
   ```yaml
   name: Rollback Deployment
   
   on:
     workflow_dispatch:
       inputs:
         environment:
           description: 'Environment to rollback'
           required: true
           type: choice
           options:
             - dev
             - staging
             - prod
         version:
           description: 'Version to rollback to'
           required: true
           type: string
   
   jobs:
     rollback:
       runs-on: ubuntu-latest
       environment: ${{ github.event.inputs.environment }}
       
       steps:
         - name: Checkout code
           uses: actions/checkout@v4
         
         - name: Configure AWS credentials
           uses: aws-actions/configure-aws-credentials@v4
           with:
             aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
             aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
             aws-region: us-east-1
         
         - name: Rollback deployment
           run: |
             echo "Rolling back ${{ github.event.inputs.environment }} to version ${{ github.event.inputs.version }}"
             .github/scripts/deploy.sh ${{ github.event.inputs.environment }} ${{ github.event.inputs.version }}
         
         - name: Verify rollback
           run: |
             .github/scripts/smoke-tests.sh ${{ github.event.inputs.environment }}
         
         - name: Notify rollback status
           if: always()
           uses: 8398a7/action-slack@v3
           with:
             status: ${{ job.status }}
             channel: '#deployments'
             webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
             text: |
               Rollback of ${{ github.event.inputs.environment }} to version ${{ github.event.inputs.version }} ${{ job.status }}
   ```

### Task 3: Test Complete Pipeline

1. **Test feature branch workflow:**
   ```bash
   # Create feature branch
   git checkout -b feature/test-cicd
   
   # Make a small change
   echo "# Test CI/CD" >> README.md
   git add README.md
   git commit -m "Test CI/CD pipeline"
   git push origin feature/test-cicd
   
   # Create pull request
   gh pr create --title "Test CI/CD Pipeline" --body "Testing the complete CI/CD pipeline"
   ```

2. **Test main branch deployment:**
   ```bash
   # Merge to main
   gh pr merge --merge
   
   # Check deployment status
   gh run list --branch main
   ```

3. **Test manual deployment:**
   ```bash
   # Trigger manual deployment
   gh workflow run ci-cd.yml --ref main -f environment=dev
   ```

### Task 4: Create Monitoring Dashboard

1. **Create `monitoring/grafana-dashboard.json`:**
   ```json
   {
     "dashboard": {
       "id": null,
       "title": "TaskManager CI/CD Pipeline",
       "tags": ["ci/cd", "taskmanager"],
       "timezone": "browser",
       "panels": [
         {
           "title": "Deployment Frequency",
           "type": "stat",
           "targets": [
             {
               "expr": "increase(github_actions_workflow_run_conclusion_total{workflow_name=\"CI/CD Pipeline\",conclusion=\"success\"}[1d])",
               "legendFormat": "Deployments per day"
             }
           ]
         },
         {
           "title": "Lead Time for Changes",
           "type": "stat",
           "targets": [
             {
               "expr": "github_actions_workflow_run_duration_seconds{workflow_name=\"CI/CD Pipeline\"}",
               "legendFormat": "Pipeline duration"
             }
           ]
         },
         {
           "title": "Deployment Success Rate",
           "type": "stat",
           "targets": [
             {
               "expr": "rate(github_actions_workflow_run_conclusion_total{workflow_name=\"CI/CD Pipeline\",conclusion=\"success\"}[1d]) / rate(github_actions_workflow_run_conclusion_total{workflow_name=\"CI/CD Pipeline\"}[1d]) * 100",
               "legendFormat": "Success rate %"
             }
           ]
         }
       ]
     }
   }
   ```

### ✅ Verification

1. **Check all workflows are working:**
   ```bash
   gh run list
   ```

2. **Verify deployments:**
   ```bash
   curl -f http://$(aws elbv2 describe-load-balancers --query "LoadBalancers[?contains(LoadBalancerName, 'taskmanager-dev')].DNSName" --output text)/health
   ```

3. **Test rollback:**
   ```bash
   gh workflow run rollback.yml -f environment=dev -f version=main-abc123
   ```

---

## Summary

In this lab, you have successfully:

✅ **Created comprehensive CI/CD pipeline structure:**
- Set up GitHub Actions workflows with proper job dependencies
- Configured secrets and environment variables
- Created reusable workflow components

✅ **Implemented automated testing and security scanning:**
- Built unit and integration test suites
- Implemented security scanning with Bandit and Safety
- Added code quality checks with Black and flake8

✅ **Configured Docker image building and ECR integration:**
- Set up automated Docker image building
- Implemented container security scanning
- Created SBOM generation for supply chain security

✅ **Deployed multi-environment deployment strategy:**
- Created environment-specific deployment jobs
- Implemented deployment scripts with instance refresh
- Added smoke testing and health checks

✅ **Tested complete CI/CD pipeline:**
- Created GitHub environments with protection rules
- Implemented rollback procedures
- Added monitoring and notification systems

## Next Steps

Your CI/CD pipeline is now fully operational and automated. In the next lab, you will:

- Set up comprehensive monitoring and alerting
- Create centralized logging with CloudWatch
- Implement performance monitoring dashboards
- Configure automated alerting for incidents

## Troubleshooting

### Common Issues

**Issue:** Pipeline fails on security scan
**Solution:**
- Review security scan results in artifacts
- Fix identified vulnerabilities
- Update dependencies to secure versions

**Issue:** Deployment fails during instance refresh
**Solution:**
- Check Auto Scaling Group configuration
- Verify launch template user data script
- Review CloudWatch logs for deployment errors

**Issue:** Environment deployment stuck pending
**Solution:**
- Check GitHub environment protection rules
- Ensure required reviewers are configured
- Verify branch protection settings

### Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS Auto Scaling Documentation](https://docs.aws.amazon.com/autoscaling/)
- [Container Security Best Practices](https://aws.amazon.com/blogs/security/best-practices-for-container-image-scanning/)

---

**🎉 Congratulations!** You have successfully completed Lab 05. Your application now has a fully automated CI/CD pipeline with comprehensive testing, security scanning, and multi-environment deployment capabilities.

**Next:** [Lab 06: Monitoring, Logging, and Alerting](./06-monitoring-logging-alerting.md)