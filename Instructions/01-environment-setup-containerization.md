# Lab 01: Environment Setup and Application Containerization

## Overview

In this lab, you will set up your development environment and containerize the Flask Task Manager application. You'll install necessary tools, configure AWS credentials, create Docker configurations, and test the containerized application.

## Objectives

After completing this lab, you will be able to:
- Install and configure AWS CLI, Terraform, Docker, and Git
- Set up AWS credentials and GitHub repository
- Create production-ready Docker configurations
- Build and test containerized applications
- Implement health checks and container optimization

## Prerequisites

- Windows 10/11, macOS, or Linux
- Administrator/sudo access for installations
- Internet connection for downloading tools
- AWS Account (free tier is sufficient)
- GitHub account

## Duration

**Estimated Time:** 60 minutes

---

## Exercise 1: Install and Configure Required Tools

### Task 1: Install AWS CLI

The AWS CLI allows you to interact with AWS services from the command line.

1. **For Windows:**
   - Download the AWS CLI installer from: https://awscli.amazonaws.com/AWSCLIV2.msi
   - Run the installer as Administrator
   - Accept the license agreement and follow the installation wizard

2. **For macOS:**
   ```bash
   # Install using Homebrew (recommended)
   brew install awscli
   
   # Alternative: Download installer
   # curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
   # sudo installer -pkg AWSCLIV2.pkg -target /
   ```

3. **For Linux:**
   ```bash
   # Download and install AWS CLI
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   ```

4. **Verify installation:**
   ```bash
   aws --version
   ```
   
   **Expected output:**
   ```
   aws-cli/2.x.x Python/3.x.x Linux/5.x.x-x source/x86_64.x
   ```

> **💡 Tip:** If `aws --version` doesn't work, you may need to restart your terminal or add AWS CLI to your PATH.

### Task 2: Install Terraform

Terraform is used for Infrastructure as Code (IaC) to manage AWS resources.

1. **For Windows:**
   - Download Terraform from: https://terraform.io/downloads
   - Extract the zip file to `C:\terraform\`
   - Add `C:\terraform\` to your system PATH:
     - Press `Win + R`, type `sysdm.cpl`, press Enter
     - Click "Advanced" tab → "Environment Variables"
     - Under "System variables", select "Path" → "Edit"
     - Click "New" and add `C:\terraform\`
     - Click "OK" to save

2. **For macOS:**
   ```bash
   # Install using Homebrew
   brew tap hashicorp/tap
   brew install hashicorp/tap/terraform
   ```

3. **For Linux:**
   ```bash
   # Download and install Terraform
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```

4. **Verify installation:**
   ```bash
   terraform --version
   ```
   
   **Expected output:**
   ```
   Terraform v1.6.0
   ```

### Task 3: Install Docker Desktop

Docker is used to containerize the application.

1. **Download Docker Desktop:**
   - Go to: https://docker.com/products/docker-desktop
   - Download for your operating system
   - Install and start Docker Desktop

2. **Verify installation:**
   ```bash
   docker --version
   docker-compose --version
   ```
   
   **Expected output:**
   ```
   Docker version 24.x.x, build xxxxxxx
   Docker Compose version v2.x.x
   ```

### Task 4: Install Git

Git is used for version control and CI/CD integration.

1. **For Windows:**
   - Download from: https://git-scm.com/downloads
   - Install with default settings

2. **For macOS:**
   ```bash
   # Install using Homebrew
   brew install git
   ```

3. **For Linux:**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install git
   
   # CentOS/RHEL
   sudo yum install git
   ```

4. **Verify installation:**
   ```bash
   git --version
   ```

### ✅ Verification

Run the following commands to verify all tools are installed:

```bash
aws --version
terraform --version
docker --version
git --version
```

All commands should return version information without errors.

---

## Exercise 2: Set up AWS Credentials and GitHub Repository

### Task 1: Create AWS Access Keys

1. **Log into AWS Management Console**
   - Go to: https://aws.amazon.com/console/
   - Sign in with your AWS account

2. **Create Access Keys:**
   - Click your username in the top-right corner
   - Select "Security credentials"
   - Scroll down to "Access keys"
   - Click "Create access key"
   - Choose "Command Line Interface (CLI)"
   - Check the confirmation box
   - Click "Next"
   - Add a description (optional): "DevOps Lab Access"
   - Click "Create access key"

3. **Download credentials:**
   - Click "Download .csv file" and save it securely
   - **⚠️ Important:** Never share these credentials or commit them to version control

### Task 2: Configure AWS CLI

1. **Run AWS configure:**
   ```bash
   aws configure
   ```

2. **Enter your credentials when prompted:**
   ```
   AWS Access Key ID [None]: YOUR_ACCESS_KEY_FROM_CSV
   AWS Secret Access Key [None]: YOUR_SECRET_KEY_FROM_CSV
   Default region name [None]: us-east-1
   Default output format [None]: json
   ```

3. **Test AWS CLI:**
   ```bash
   aws sts get-caller-identity
   ```
   
   **Expected output:**
   ```json
   {
       "UserId": "AIDACKCEVSQ6C2EXAMPLE",
       "Account": "123456789012",
       "Arn": "arn:aws:iam::123456789012:user/DevOps-User"
   }
   ```

### Task 3: Create GitHub Repository

1. **Go to GitHub:**
   - Navigate to: https://github.com/
   - Sign in to your account

2. **Create new repository:**
   - Click "New repository" (green button)
   - Repository name: `task-manager-devops`
   - Description: `Multi-environment Flask app deployment with DevOps practices`
   - Select "Public" (or Private if you prefer)
   - Check "Add a README file"
   - Add `.gitignore` template: "Python"
   - Click "Create repository"

3. **Clone repository to your local machine:**
   ```bash
   # Navigate to your desired directory
   cd ~/Desktop/Projects  # or your preferred location
   
   # Clone the repository
   git clone https://github.com/YOUR_USERNAME/task-manager-devops.git
   cd task-manager-devops
   ```

### ✅ Verification

1. **AWS CLI configured:**
   ```bash
   aws sts get-caller-identity
   ```
   Should return your AWS account information.

2. **GitHub repository cloned:**
   ```bash
   ls -la
   ```
   Should show `.git` folder and `README.md`.

---

## Exercise 3: Create Docker Configuration Files

### Task 1: Set up Project Structure

1. **Copy application files:**
   ```bash
   # Copy all files from the original project to your new repo
   # (You'll need to copy app.py, models.py, routes.py, etc.)
   ```

2. **Create directory structure:**
   ```bash
   mkdir -p docker
   mkdir -p tests
   mkdir -p scripts
   ```

### Task 2: Create Production-Ready Dockerfile

1. **Create `Dockerfile` in project root:**
   ```dockerfile
   # Multi-stage build for smaller final image
   FROM python:3.9-slim as builder
   
   # Set working directory
   WORKDIR /app
   
   # Install build dependencies
   RUN apt-get update && apt-get install -y \
       gcc \
       && rm -rf /var/lib/apt/lists/*
   
   # Copy and install Python dependencies
   COPY requirements.txt .
   RUN pip install --user --no-cache-dir -r requirements.txt
   
   # Production stage
   FROM python:3.9-slim
   
   # Set working directory
   WORKDIR /app
   
   # Install runtime dependencies
   RUN apt-get update && apt-get install -y \
       curl \
       && rm -rf /var/lib/apt/lists/*
   
   # Copy installed packages from builder stage
   COPY --from=builder /root/.local /root/.local
   
   # Copy application code
   COPY . .
   
   # Create non-root user for security
   RUN adduser --disabled-password --gecos '' --uid 1000 appuser && \
       chown -R appuser:appuser /app
   
   # Switch to non-root user
   USER appuser
   
   # Make sure scripts in .local are usable
   ENV PATH=/root/.local/bin:$PATH
   
   # Expose application port
   EXPOSE 5000
   
   # Health check
   HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
       CMD curl -f http://localhost:5000/health || exit 1
   
   # Run application
   CMD ["python", "app.py"]
   ```

2. **Create `.dockerignore` file:**
   ```
   # Version control
   .git
   .gitignore
   
   # Python
   __pycache__/
   *.py[cod]
   *$py.class
   .Python
   venv/
   .venv/
   env/
   .env
   
   # IDEs
   .vscode/
   .idea/
   *.swp
   *.swo
   
   # OS
   .DS_Store
   Thumbs.db
   
   # Logs
   *.log
   logs/
   
   # Testing
   .pytest_cache/
   .coverage
   htmlcov/
   
   # Documentation
   README.md
   *.md
   
   # Docker
   Dockerfile
   docker-compose.yml
   .dockerignore
   
   # Terraform
   terraform/
   *.tfstate
   *.tfvars
   
   # Node modules (if any)
   node_modules/
   
   # Build artifacts
   build/
   dist/
   ```

### Task 3: Create Docker Compose Configuration

1. **Create `docker-compose.yml`:**
   ```yaml
   version: '3.8'
   
   services:
     web:
       build: .
       ports:
         - "5000:5000"
       environment:
         - FLASK_ENV=development
         - FLASK_DEBUG=true
         - DATABASE_URL=postgresql://taskuser:taskpass@db:5432/taskmanager
         - SECRET_KEY=dev-secret-key-change-in-production
       depends_on:
         db:
           condition: service_healthy
       volumes:
         - ./logs:/app/logs
       networks:
         - app-network
       restart: unless-stopped
   
     db:
       image: postgres:13-alpine
       environment:
         - POSTGRES_USER=taskuser
         - POSTGRES_PASSWORD=taskpass
         - POSTGRES_DB=taskmanager
         - POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256
       volumes:
         - postgres_data:/var/lib/postgresql/data
         - ./init_db.sql:/docker-entrypoint-initdb.d/init_db.sql
       ports:
         - "5432:5432"
       networks:
         - app-network
       healthcheck:
         test: ["CMD-SHELL", "pg_isready -U taskuser -d taskmanager"]
         interval: 10s
         timeout: 5s
         retries: 5
         start_period: 30s
       restart: unless-stopped
   
   volumes:
     postgres_data:
       driver: local
   
   networks:
     app-network:
       driver: bridge
   ```

2. **Create `docker-compose.override.yml` for development:**
   ```yaml
   version: '3.8'
   
   services:
     web:
       volumes:
         - .:/app
       environment:
         - FLASK_ENV=development
         - FLASK_DEBUG=true
       command: ["python", "app.py"]
   
     db:
       ports:
         - "5432:5432"
   ```

### ✅ Verification

1. **Check files created:**
   ```bash
   ls -la
   ```
   Should show `Dockerfile`, `.dockerignore`, and `docker-compose.yml`.

2. **Validate Docker configuration:**
   ```bash
   docker-compose config
   ```
   Should display the composed configuration without errors.

---

## Exercise 4: Build and Test Containerized Application

### Task 1: Build Docker Image

1. **Build the application image:**
   ```bash
   docker-compose build
   ```
   
   **Expected output:**
   ```
   Building web
   Step 1/15 : FROM python:3.9-slim as builder
   ...
   Successfully built [image-id]
   Successfully tagged [project-name]_web:latest
   ```

2. **Verify image size optimization:**
   ```bash
   docker images | grep -E "(REPOSITORY|task-manager|web)"
   ```
   
   The multi-stage build should result in a smaller final image.

### Task 2: Start Application Services

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```
   
   **Expected output:**
   ```
   Creating network "task-manager-devops_app-network" with driver "bridge"
   Creating volume "task-manager-devops_postgres_data" with local driver
   Creating task-manager-devops_db_1 ... done
   Creating task-manager-devops_web_1 ... done
   ```

2. **Check service status:**
   ```bash
   docker-compose ps
   ```
   
   **Expected output:**
   ```
   Name                    Command               State           Ports
   ----------------------------------------------------------------------
   task-manager-devops_db_1    docker-entrypoint.sh postgres   Up      5432/tcp
   task-manager-devops_web_1   python app.py                    Up      0.0.0.0:5000->5000/tcp
   ```

### Task 3: Test Application Functionality

1. **Wait for services to be ready:**
   ```bash
   # Wait for database to be ready
   docker-compose logs db | grep "ready to accept connections"
   
   # Wait for web application to start
   docker-compose logs web | grep "Running on"
   ```

2. **Test health endpoint:**
   ```bash
   curl -s http://localhost:5000/health | jq .
   ```
   
   **Expected output:**
   ```json
   {
     "status": "healthy",
     "database": "connected",
     "timestamp": "2024-01-01T10:00:00.000000"
   }
   ```

3. **Test API endpoints:**
   ```bash
   # Test users endpoint
   curl -s http://localhost:5000/api/users | jq .
   
   # Test dashboard stats
   curl -s http://localhost:5000/api/dashboard-stats | jq .
   ```

4. **Test web interface:**
   - Open browser to: http://localhost:5000
   - Verify the dashboard loads correctly
   - Navigate to Tasks and Users sections

### Task 4: Initialize Database with Sample Data

1. **Initialize database:**
   ```bash
   docker-compose exec web python init_db.py --sample-data
   ```
   
   **Expected output:**
   ```
   Dropped existing tables
   Created database tables
   Created 3 users and 8 tasks
   Database initialization completed successfully!
   ```

2. **Verify sample data:**
   ```bash
   curl -s http://localhost:5000/api/users | jq '.users | length'
   curl -s http://localhost:5000/api/tasks | jq '.tasks | length'
   ```

### ✅ Verification

1. **All services running:**
   ```bash
   docker-compose ps
   ```
   All services should show "Up" status.

2. **Health check passing:**
   ```bash
   curl -f http://localhost:5000/health
   ```
   Should return 200 OK.

3. **Database connectivity:**
   ```bash
   docker-compose exec db psql -U taskuser -d taskmanager -c "SELECT COUNT(*) FROM users;"
   ```
   Should return count of users.

---

## Exercise 5: Implement Health Checks and Optimization

### Task 1: Configure Application Health Checks

1. **Test Docker health check:**
   ```bash
   docker-compose ps
   ```
   The web service should show "healthy" status.

2. **Check health check logs:**
   ```bash
   docker inspect $(docker-compose ps -q web) | jq '.[0].State.Health'
   ```

### Task 2: Optimize Docker Image

1. **Check current image size:**
   ```bash
   docker images | grep web
   ```

2. **Analyze image layers:**
   ```bash
   docker history $(docker-compose images -q web)
   ```

3. **Clean up unused images:**
   ```bash
   docker image prune -f
   ```

### Task 3: Configure Logging

1. **Create logs directory:**
   ```bash
   mkdir -p logs
   ```

2. **View application logs:**
   ```bash
   docker-compose logs -f web
   ```

3. **View database logs:**
   ```bash
   docker-compose logs -f db
   ```

### Task 4: Test Container Restart and Recovery

1. **Stop web container:**
   ```bash
   docker-compose stop web
   ```

2. **Verify automatic restart:**
   ```bash
   docker-compose start web
   ```

3. **Test application recovery:**
   ```bash
   # Wait a moment for startup
   sleep 30
   curl -f http://localhost:5000/health
   ```

### ✅ Verification

1. **Health checks working:**
   ```bash
   docker-compose ps
   ```
   Services should show "healthy" status.

2. **Logs accessible:**
   ```bash
   ls -la logs/
   ```
   Should contain application log files.

3. **Performance optimized:**
   ```bash
   docker images | grep web
   ```
   Image should be reasonably sized (< 500MB).

---

## Summary

In this lab, you have successfully:

✅ **Installed and configured essential DevOps tools:**
- AWS CLI for cloud resource management
- Terraform for infrastructure as code
- Docker for containerization
- Git for version control

✅ **Set up AWS credentials and GitHub repository:**
- Created secure AWS access keys
- Configured AWS CLI with proper credentials
- Created and cloned GitHub repository

✅ **Created production-ready Docker configurations:**
- Multi-stage Dockerfile for optimized images
- Comprehensive docker-compose setup
- Proper security with non-root user
- Health checks and monitoring

✅ **Built and tested containerized application:**
- Successfully built and deployed containers
- Verified application functionality
- Tested database connectivity
- Initialized with sample data

✅ **Implemented optimization and monitoring:**
- Configured health checks
- Optimized Docker image size
- Set up logging and monitoring
- Tested recovery scenarios

## Next Steps

Your application is now containerized and ready for cloud deployment. In the next lab, you will:

- Create Terraform modules for AWS infrastructure
- Set up VPC, subnets, and security groups
- Deploy networking foundation to AWS
- Configure environment-specific settings

## Troubleshooting

### Common Issues

**Issue:** `aws --version` command not found
**Solution:** 
- Restart terminal after installation
- Add AWS CLI to PATH manually
- Verify installation completed successfully

**Issue:** Docker daemon not running
**Solution:**
- Start Docker Desktop application
- Check Docker service status
- Restart Docker service if needed

**Issue:** Permission denied accessing Docker
**Solution:**
- Add user to docker group: `sudo usermod -aG docker $USER`
- Restart terminal or log out/in
- Use `sudo` prefix for Docker commands (not recommended for production)

**Issue:** Database connection failed
**Solution:**
- Check if PostgreSQL container is healthy: `docker-compose ps`
- Verify database logs: `docker-compose logs db`
- Ensure database initialization completed

### Additional Resources

- [AWS CLI Documentation](https://docs.aws.amazon.com/cli/)
- [Terraform Documentation](https://terraform.io/docs)
- [Docker Documentation](https://docs.docker.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

**🎉 Congratulations!** You have successfully completed Lab 01. Your development environment is now set up and your application is containerized and ready for deployment.

**Next:** [Lab 02: Infrastructure Foundation with Terraform](./02-infrastructure-foundation-terraform.md)