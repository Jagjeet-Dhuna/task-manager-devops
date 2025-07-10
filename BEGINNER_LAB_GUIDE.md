# Multi-Environment Web App Deployment: Beginner Lab Guide

## 🎯 Welcome to Your DevOps Journey!

This guide will hold your hand through every step of deploying a Flask application to AWS using modern DevOps practices. Don't worry if you're new to this - we'll explain everything as we go!

**What You'll Build:** A complete multi-environment deployment system for the Task Manager application.

**Time Required:** 8-10 hours (perfect for a weekend project!)

---

## 📋 Before We Start - Let's Set Up Your Computer

### What You Need to Install

Don't worry - I'll walk you through each installation step by step!

#### Step 1: Install AWS CLI
```bash
# For Windows (using PowerShell as Administrator)
# Download and run: https://awscli.amazonaws.com/AWSCLIV2.msi

# For Mac (using Homebrew package manager)
brew install awscli

# For Linux (downloads and installs AWS CLI)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip        # Extract the downloaded file
sudo ./aws/install       # Install with admin privileges
```

> 💡 **What is AWS CLI?** The AWS Command Line Interface is a tool that lets you interact with AWS services from your terminal instead of using the web console. It's essential for automation and scripting.

**Test it worked:**
```bash
aws --version
# Should show: aws-cli/2.x.x
```

#### Step 2: Install Terraform
```bash
# For Windows
# Download from: https://terraform.io/downloads
# Extract to C:\terraform\
# Add C:\terraform\ to your PATH

# For Mac
brew install terraform

# For Linux
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

**Test it worked:**
```bash
terraform --version
# Should show: Terraform v1.6.0
```

#### Step 3: Install Docker Desktop
- Go to https://docker.com/products/docker-desktop
- Download and install for your operating system
- Start Docker Desktop

**Test it worked:**
```bash
docker --version
# Should show: Docker version 24.x.x
```

#### Step 4: Install Git
```bash
# For Windows
# Download from: https://git-scm.com/downloads

# For Mac
brew install git

# For Linux
sudo apt-get install git
```

**Test it worked:**
```bash
git --version
# Should show: git version 2.x.x
```

### Setting Up Your Accounts

#### Create AWS Account
1. Go to https://aws.amazon.com/
2. Click "Create an AWS Account"
3. Fill in your information
4. Add a payment method (don't worry - we'll use free tier resources)
5. Verify your phone number
6. Choose "Basic Support Plan" (free)

#### Create GitHub Account
1. Go to https://github.com/
2. Click "Sign up"
3. Choose a username and password
4. Verify your email

### Configure AWS CLI
```bash
# Run this command and follow the prompts
aws configure

# When prompted, enter:
# AWS Access Key ID: [We'll get this from AWS Console]
# AWS Secret Access Key: [We'll get this from AWS Console]
# Default region name: us-east-1
# Default output format: json
```

> 🔐 **Security Note:** These credentials give full access to your AWS account. Never share them or commit them to version control. The `aws configure` command stores them securely in `~/.aws/credentials`.

**How to get your AWS keys:**
1. Log into AWS Console
2. Click your username (top right)
3. Click "Security credentials"
4. Click "Create access key"
5. Download the CSV file
6. Use the keys from the file

---

## 🐳 LAB 1: Making Your App Work in a Container (45 minutes)

### What is Docker and Why Do We Need It?

Think of Docker like a lunch box for your application. Just like a lunch box keeps your food fresh and separate from other lunches, Docker keeps your app and all its dependencies together in a "container" that can run anywhere.

### Step 1: Create a Dockerfile

A Dockerfile is like a recipe that tells Docker how to build your container.

**Create a file called `Dockerfile` in your project root directory:**

```dockerfile
# Start with a base image that has Python installed
FROM python:3.9-slim

# This is like setting up a workspace in the container
WORKDIR /app

# Install system tools we might need
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first (this helps with caching)
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy all our application code
COPY . .

# Create a user that isn't root (this is safer)
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Tell Docker which port our app uses
EXPOSE 5000

# Add a health check so we know if the app is working
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# This command runs when the container starts
CMD ["python", "app.py"]
```

### Step 2: Create a Docker Compose File

Docker Compose lets us run multiple containers together (like our app and database).

**Create a file called `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  # This is our web application
  web:
    build: .  # Build from our Dockerfile
    ports:
      - "5000:5000"  # Map port 5000 on your computer to port 5000 in container
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=true
      - DATABASE_URL=postgresql://taskuser:taskpass@db:5432/taskmanager
    depends_on:
      db:
        condition: service_healthy  # Wait for database to be ready
    volumes:
      - ./logs:/app/logs  # Share logs folder with your computer
    restart: unless-stopped

  # This is our database
  db:
    image: postgres:13-alpine  # Use a pre-built PostgreSQL image
    environment:
      - POSTGRES_USER=taskuser
      - POSTGRES_PASSWORD=taskpass
      - POSTGRES_DB=taskmanager
    volumes:
      - postgres_data:/var/lib/postgresql/data  # Store database data
    ports:
      - "5432:5432"  # Map database port
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U taskuser -d taskmanager"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

# This creates a persistent volume for our database
volumes:
  postgres_data:
```

### Step 3: Create a .dockerignore File

This tells Docker which files to ignore when building the container.

**Create a file called `.dockerignore`:**

```
.git
.gitignore
README.md
Dockerfile
docker-compose.yml
.env
venv/
__pycache__/
*.pyc
.pytest_cache/
.coverage
.vscode/
node_modules/
```

### Step 4: Test Your Containerized App

Let's make sure everything works!

```bash
# Open a terminal in your project directory

# Build and start the containers
docker-compose up --build

# You should see lots of text scrolling by
# Look for messages like:
# - "database system is ready to accept connections"
# - "Running on http://0.0.0.0:5000"
```

**Open another terminal and test:**

```bash
# Test the health check
curl http://localhost:5000/health

# Should return: {"status": "healthy", "database": "connected", ...}

# Test the API
curl http://localhost:5000/api/users

# Should return: {"users": [...], "pagination": {...}}
```

**To stop the containers:**
```bash
# Press Ctrl+C in the first terminal, then run:
docker-compose down
```

> 🛑 **What does `docker-compose down` do?**
> - Stops all running containers
> - Removes the containers and networks created by `docker-compose up`
> - Preserves volumes (so your database data isn't lost)
> - Use `docker-compose down -v` to also remove volumes

### 🎉 Lab 1 Complete!

**What did we just do?**
- Created a Docker container for your Flask app
- Set up a PostgreSQL database in a container
- Made them work together with Docker Compose
- Tested that everything works

**Why is this important?**
- Your app now runs the same way on any computer
- You can easily share your entire development environment
- This is the foundation for deploying to the cloud

---

## 🏗️ LAB 2: Building Your Cloud Infrastructure (60 minutes)

### What is Infrastructure as Code?

Instead of clicking around in the AWS console to create resources, we'll write "code" that describes what we want AWS to build for us. This way, we can recreate our infrastructure anytime and it will always be the same.

### Step 1: Understanding What We're Building

We're going to create:
- **VPC**: A private network in AWS (like your home network)
- **Subnets**: Smaller networks inside the VPC (like rooms in your house)
- **Security Groups**: Firewalls that control who can talk to what
- **Internet Gateway**: The door to the internet

### Step 2: Create the Terraform Project Structure

```bash
# Create directories for our Terraform code
mkdir -p terraform/modules/vpc
mkdir -p terraform/modules/security-groups
mkdir -p terraform/modules/ec2
mkdir -p terraform/modules/rds
mkdir -p terraform/modules/alb
mkdir -p terraform/modules/monitoring
mkdir -p terraform/environments/dev
mkdir -p terraform/environments/staging
mkdir -p terraform/environments/prod
```

### Step 3: Create the VPC Module

Think of this as creating your private cloud network.

**Create `terraform/modules/vpc/main.tf`:**

```hcl
# This creates your private cloud network
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.environment}-vpc"
    Environment = var.environment
    Project     = "TaskManager"
  }
}

# This is like the front door to the internet
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "${var.environment}-igw"
    Environment = var.environment
    Project     = "TaskManager"
  }
}

# These are public subnets (accessible from internet)
resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.environment}-public-subnet-${count.index + 1}"
    Environment = var.environment
    Project     = "TaskManager"
    Type        = "Public"
  }
}

# These are private subnets (not accessible from internet)
resource "aws_subnet" "private" {
  count             = length(var.private_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name        = "${var.environment}-private-subnet-${count.index + 1}"
    Environment = var.environment
    Project     = "TaskManager"
    Type        = "Private"
  }
}

# This is a routing table for public subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  # Route internet traffic through the internet gateway
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name        = "${var.environment}-public-rt"
    Environment = var.environment
    Project     = "TaskManager"
  }
}

# Connect public subnets to the public route table
resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# NAT Gateway allows private subnets to access the internet
resource "aws_nat_gateway" "main" {
  count         = length(aws_subnet.public)
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name        = "${var.environment}-nat-${count.index + 1}"
    Environment = var.environment
    Project     = "TaskManager"
  }

  depends_on = [aws_internet_gateway.main]
}

# Elastic IP for NAT Gateway
resource "aws_eip" "nat" {
  count  = length(aws_subnet.public)
  domain = "vpc"

  tags = {
    Name        = "${var.environment}-nat-eip-${count.index + 1}"
    Environment = var.environment
    Project     = "TaskManager"
  }
}

# Route tables for private subnets
resource "aws_route_table" "private" {
  count  = length(aws_subnet.private)
  vpc_id = aws_vpc.main.id

  # Route internet traffic through NAT Gateway
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = {
    Name        = "${var.environment}-private-rt-${count.index + 1}"
    Environment = var.environment
    Project     = "TaskManager"
  }
}

# Connect private subnets to their route tables
resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}
```

**Create `terraform/modules/vpc/variables.tf`:**

```hcl
variable "environment" {
  description = "Environment name (like dev, staging, prod)"
  type        = string
}

variable "vpc_cidr" {
  description = "IP address range for the VPC"
  type        = string
}

variable "public_subnet_cidrs" {
  description = "IP address ranges for public subnets"
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "IP address ranges for private subnets"
  type        = list(string)
}

variable "availability_zones" {
  description = "AWS availability zones to use"
  type        = list(string)
}
```

**Create `terraform/modules/vpc/outputs.tf`:**

```hcl
output "vpc_id" {
  description = "ID of the VPC we created"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

output "vpc_cidr_block" {
  description = "IP range of the VPC"
  value       = aws_vpc.main.cidr_block
}
```

### Step 4: Create Security Groups

These are like firewalls that control network traffic.

**Create `terraform/modules/security-groups/main.tf`:**

```hcl
# Security group for the load balancer
resource "aws_security_group" "alb" {
  name        = "${var.environment}-alb-sg"
  description = "Allow HTTP and HTTPS traffic from internet"
  vpc_id      = var.vpc_id

  # Allow HTTP traffic from anywhere
  ingress {
    description = "HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow HTTPS traffic from anywhere
  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.environment}-alb-sg"
    Environment = var.environment
    Project     = "TaskManager"
  }
}

# Security group for web servers
resource "aws_security_group" "web" {
  name        = "${var.environment}-web-sg"
  description = "Allow traffic from load balancer to web servers"
  vpc_id      = var.vpc_id

  # Allow traffic from load balancer on port 5000
  ingress {
    description     = "Application traffic from load balancer"
    from_port       = 5000
    to_port         = 5000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # Allow SSH from within VPC (for debugging)
  ingress {
    description = "SSH from within VPC"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr_block]
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.environment}-web-sg"
    Environment = var.environment
    Project     = "TaskManager"
  }
}

# Security group for database
resource "aws_security_group" "db" {
  name        = "${var.environment}-db-sg"
  description = "Allow database access from web servers only"
  vpc_id      = var.vpc_id

  # Allow PostgreSQL traffic from web servers only
  ingress {
    description     = "PostgreSQL from web servers"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.web.id]
  }

  tags = {
    Name        = "${var.environment}-db-sg"
    Environment = var.environment
    Project     = "TaskManager"
  }
}
```

**Create `terraform/modules/security-groups/variables.tf`:**

```hcl
variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "vpc_cidr_block" {
  description = "IP range of the VPC"
  type        = string
}
```

**Create `terraform/modules/security-groups/outputs.tf`:**

```hcl
output "alb_security_group_id" {
  description = "Security group ID for load balancer"
  value       = aws_security_group.alb.id
}

output "web_security_group_id" {
  description = "Security group ID for web servers"
  value       = aws_security_group.web.id
}

output "db_security_group_id" {
  description = "Security group ID for database"
  value       = aws_security_group.db.id
}
```

### Step 5: Create Your First Environment

**Create `terraform/environments/dev/main.tf`:**

```hcl
# This tells Terraform which version to use
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# This configures the AWS provider
provider "aws" {
  region = var.aws_region
}

# Use our VPC module
module "vpc" {
  source = "../../modules/vpc"

  environment            = var.environment
  vpc_cidr              = var.vpc_cidr
  public_subnet_cidrs   = var.public_subnet_cidrs
  private_subnet_cidrs  = var.private_subnet_cidrs
  availability_zones    = var.availability_zones
}

# Use our security groups module
module "security_groups" {
  source = "../../modules/security-groups"

  environment     = var.environment
  vpc_id          = module.vpc.vpc_id
  vpc_cidr_block  = module.vpc.vpc_cidr_block
}
```

**Create `terraform/environments/dev/variables.tf`:**

```hcl
variable "aws_region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "IP range for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "IP ranges for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "IP ranges for private subnets"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "availability_zones" {
  description = "AWS availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}
```

**Create `terraform/environments/dev/outputs.tf`:**

```hcl
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = module.vpc.private_subnet_ids
}
```

### Step 6: Deploy Your Infrastructure

Time to create your cloud infrastructure!

```bash
# Navigate to the dev environment
cd terraform/environments/dev

# Initialize Terraform (download the AWS provider)
terraform init

# Check what Terraform wants to create
terraform plan

# Create the infrastructure (type 'yes' when prompted)
terraform apply
```

> 🏗️ **Terraform Commands Explained:**
> - `terraform init`: Downloads required providers and initializes the working directory
> - `terraform plan`: Shows what changes Terraform will make (like a preview)
> - `terraform apply`: Actually creates/modifies the infrastructure
> - Always run `plan` before `apply` to avoid surprises!

**You should see output like:**
```
Apply complete! Resources: 15 added, 0 changed, 0 destroyed.

Outputs:
vpc_id = "vpc-1234567890abcdef0"
public_subnet_ids = [
  "subnet-0123456789abcdef0",
  "subnet-0123456789abcdef1"
]
private_subnet_ids = [
  "subnet-0123456789abcdef2",
  "subnet-0123456789abcdef3"
]
```

### Step 7: Verify in AWS Console

1. Log into AWS Console
2. Go to VPC service
3. You should see your new VPC named "dev-vpc"
4. Check subnets - you should see 4 subnets (2 public, 2 private)
5. Check security groups - you should see 3 new security groups

### 🎉 Lab 2 Complete!

**What did we just do?**
- Created a Virtual Private Cloud (VPC) in AWS
- Set up public and private subnets across multiple availability zones
- Created security groups to control network access
- Used Terraform to manage everything as code

**Why is this important?**
- This is the foundation for all your cloud resources
- Everything is reproducible and version-controlled
- You can create identical environments for dev, staging, and production

---

## 🗄️ LAB 3: Setting Up Your Database (45 minutes)

### What is Amazon RDS?

RDS (Relational Database Service) is AWS's managed database service. Instead of installing and managing PostgreSQL yourself, AWS handles backups, updates, and scaling for you.

### Step 1: Create the RDS Module

**Create `terraform/modules/rds/main.tf`:**

```hcl
# This groups our private subnets for the database
resource "aws_db_subnet_group" "main" {
  name       = "${var.environment}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "${var.environment}-db-subnet-group"
    Environment = var.environment
    Project     = "TaskManager"
  }
}

# This configures database settings
resource "aws_db_parameter_group" "main" {
  family = "postgres13"
  name   = "${var.environment}-db-params"

  # Enable logging for troubleshooting
  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name  = "log_statement"
    value = "all"
  }

  tags = {
    Name        = "${var.environment}-db-params"
    Environment = var.environment
    Project     = "TaskManager"
  }
}

# This creates the actual database
resource "aws_db_instance" "main" {
  identifier = "${var.environment}-taskmanager-db"
  
  # Database engine configuration
  engine         = "postgres"
  engine_version = "13.13"
  instance_class = var.db_instance_class
  
  # Storage configuration
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type         = "gp2"
  storage_encrypted    = true
  
  # Database credentials
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  
  # Network configuration
  vpc_security_group_ids = [var.db_security_group_id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  publicly_accessible    = false  # Keep it private!
  
  # Backup configuration
  backup_retention_period   = var.backup_retention_period
  backup_window            = var.backup_window
  maintenance_window       = var.maintenance_window
  delete_automated_backups = var.environment == "dev"
  
  # Use our parameter group
  parameter_group_name = aws_db_parameter_group.main.name
  
  # Snapshot configuration
  skip_final_snapshot       = var.environment == "dev"
  final_snapshot_identifier = var.environment != "dev" ? "${var.environment}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null
  
  # Monitoring
  monitoring_interval = var.monitoring_interval
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  
  # Security - only protect production from accidental deletion
  deletion_protection = var.environment == "prod"
  
  tags = {
    Name        = "${var.environment}-taskmanager-db"
    Environment = var.environment
    Project     = "TaskManager"
  }
}
```

**Create `terraform/modules/rds/variables.tf`:**

```hcl
variable "environment" {
  description = "Environment name"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for database"
  type        = list(string)
}

variable "db_security_group_id" {
  description = "Security group ID for database"
  type        = string
}

variable "db_instance_class" {
  description = "Database instance size"
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "Initial storage size in GB"
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Maximum storage size in GB"
  type        = number
  default     = 100
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "taskmanager"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "taskuser"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "backup_retention_period" {
  description = "How many days to keep backups"
  type        = number
  default     = 7
}

variable "backup_window" {
  description = "When to run backups (UTC)"
  type        = string
  default     = "07:00-09:00"
}

variable "maintenance_window" {
  description = "When to do maintenance (UTC)"
  type        = string
  default     = "sun:05:00-sun:07:00"
}

variable "monitoring_interval" {
  description = "Enhanced monitoring interval in seconds"
  type        = number
  default     = 60
}
```

**Create `terraform/modules/rds/outputs.tf`:**

```hcl
output "db_endpoint" {
  description = "Database connection endpoint"
  value       = aws_db_instance.main.endpoint
}

output "db_port" {
  description = "Database port"
  value       = aws_db_instance.main.port
}

output "db_instance_id" {
  description = "Database instance ID"
  value       = aws_db_instance.main.id
}

output "db_name" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}
```

### Step 2: Update Your Dev Environment

**Update `terraform/environments/dev/main.tf` (add this to the end):**

```hcl
# Add the RDS module
module "rds" {
  source = "../../modules/rds"

  environment           = var.environment
  private_subnet_ids    = module.vpc.private_subnet_ids
  db_security_group_id  = module.security_groups.db_security_group_id
  db_instance_class     = var.db_instance_class
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  db_password          = var.db_password
  backup_retention_period = var.backup_retention_period
}
```

**Add to `terraform/environments/dev/variables.tf`:**

```hcl
variable "db_instance_class" {
  description = "Database instance size"
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "Initial database storage in GB"
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Maximum database storage in GB"
  type        = number
  default     = 50
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "backup_retention_period" {
  description = "Days to keep database backups"
  type        = number
  default     = 1
}
```

**Add to `terraform/environments/dev/outputs.tf`:**

```hcl
output "db_endpoint" {
  description = "Database endpoint"
  value       = module.rds.db_endpoint
}
```

### Step 3: Deploy Your Database

```bash
# Make sure you're in the dev environment directory
cd terraform/environments/dev

# Set a secure password for your database
export TF_VAR_db_password="MySecurePassword123!"

# Plan the changes
terraform plan

# Apply the changes (this will take about 10 minutes)
terraform apply
```

**You should see output like:**
```
Apply complete! Resources: 3 added, 0 changed, 0 destroyed.

Outputs:
db_endpoint = "dev-taskmanager-db.c1234567890.us-east-1.rds.amazonaws.com"
vpc_id = "vpc-1234567890abcdef0"
...
```

### Step 4: Verify Your Database

1. Go to AWS Console
2. Navigate to RDS service
3. Click on "Databases"
4. You should see "dev-taskmanager-db" with status "Available"
5. Click on it to see details - note the endpoint address

### 🎉 Lab 3 Complete!

**What did we just do?**
- Created a managed PostgreSQL database in AWS
- Put it in private subnets (not accessible from internet)
- Configured automatic backups and monitoring
- Set up security groups to only allow access from web servers

**Why is this important?**
- AWS manages the database for us (backups, updates, scaling)
- It's secure and highly available
- Our application can connect to it from EC2 instances

---

## 🖥️ LAB 4: Web Servers and Load Balancer (75 minutes)

### What Are We Building?

We're creating:
- **Application Load Balancer (ALB)**: Distributes traffic across multiple servers
- **Auto Scaling Group**: Automatically adds/removes servers based on demand
- **EC2 Instances**: Virtual servers that run your application

### Step 1: Create the Application Load Balancer Module

**Create `terraform/modules/alb/main.tf`:**

```hcl
# This creates the load balancer
resource "aws_lb" "main" {
  name               = "${var.environment}-alb"
  internal           = false  # Internet-facing
  load_balancer_type = "application"
  security_groups    = [var.alb_security_group_id]
  subnets            = var.public_subnet_ids

  # Only enable deletion protection in production
  enable_deletion_protection = var.environment == "prod"

  tags = {
    Name        = "${var.environment}-alb"
    Environment = var.environment
    Project     = "TaskManager"
  }
}

# This defines what the load balancer should route to
resource "aws_lb_target_group" "web" {
  name     = "${var.environment}-web-tg"
  port     = 5000
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  # Health check configuration
  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name        = "${var.environment}-web-tg"
    Environment = var.environment
    Project     = "TaskManager"
  }
}

# This tells the load balancer how to handle requests
resource "aws_lb_listener" "web" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
}
```

**Create `terraform/modules/alb/variables.tf`:**

```hcl
variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs"
  type        = list(string)
}

variable "alb_security_group_id" {
  description = "Security group ID for ALB"
  type        = string
}
```

**Create `terraform/modules/alb/outputs.tf`:**

```hcl
output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = aws_lb.main.zone_id
}

output "target_group_arn" {
  description = "ARN of the target group"
  value       = aws_lb_target_group.web.arn
}

output "alb_arn_suffix" {
  description = "ARN suffix of the load balancer"
  value       = aws_lb.main.arn_suffix
}
```

### Step 2: Create the EC2 Module

**Create `terraform/modules/ec2/main.tf`:**

```hcl
# Get the latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Create an IAM role for EC2 instances
resource "aws_iam_role" "ec2_role" {
  name = "${var.environment}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# Give the EC2 role necessary permissions
resource "aws_iam_role_policy" "ec2_policy" {
  name = "${var.environment}-ec2-policy"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      }
    ]
  })
}

# Create an instance profile
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.environment}-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

# Create a launch template
resource "aws_launch_template" "web" {
  name_prefix   = "${var.environment}-web-"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type
  key_name      = var.key_name

  vpc_security_group_ids = [var.web_security_group_id]

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    environment = var.environment
    db_host     = var.db_endpoint
    db_name     = var.db_name
    db_username = var.db_username
    db_password = var.db_password
  }))

  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_profile.name
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "${var.environment}-web-instance"
      Environment = var.environment
      Project     = "TaskManager"
    }
  }
}

# Create an Auto Scaling Group
resource "aws_autoscaling_group" "web" {
  name                = "${var.environment}-web-asg"
  vpc_zone_identifier = var.private_subnet_ids
  min_size            = var.min_size
  max_size            = var.max_size
  desired_capacity    = var.desired_capacity
  target_group_arns   = [var.target_group_arn]
  health_check_type   = "ELB"
  health_check_grace_period = 300

  launch_template {
    id      = aws_launch_template.web.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.environment}-web-asg"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "Project"
    value               = "TaskManager"
    propagate_at_launch = true
  }
}
```

**Create `terraform/modules/ec2/variables.tf`:**

```hcl
variable "environment" {
  description = "Environment name"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "EC2 Key Pair name"
  type        = string
  default     = null
}

variable "private_subnet_ids" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "web_security_group_id" {
  description = "Security group ID for web servers"
  type        = string
}

variable "target_group_arn" {
  description = "Target group ARN"
  type        = string
}

variable "min_size" {
  description = "Minimum number of instances"
  type        = number
  default     = 1
}

variable "max_size" {
  description = "Maximum number of instances"
  type        = number
  default     = 3
}

variable "desired_capacity" {
  description = "Desired number of instances"
  type        = number
  default     = 1
}

variable "db_endpoint" {
  description = "Database endpoint"
  type        = string
}

variable "db_name" {
  description = "Database name"
  type        = string
}

variable "db_username" {
  description = "Database username"
  type        = string
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}
```

**Create `terraform/modules/ec2/outputs.tf`:**

```hcl
output "asg_name" {
  description = "Auto Scaling Group name"
  value       = aws_autoscaling_group.web.name
}

output "asg_arn" {
  description = "Auto Scaling Group ARN"
  value       = aws_autoscaling_group.web.arn
}
```

### Step 3: Create the User Data Script

This script runs when each EC2 instance starts up.

**Create `terraform/modules/ec2/user_data.sh`:**

```bash
#!/bin/bash

# Update the system
yum update -y

# Install Docker
yum install -y docker git
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create application directory
mkdir -p /app
cd /app

# Clone your application (you'll need to update this with your actual repo)
# For now, we'll create a simple setup
cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "app.py"]
EOF

# Create a basic docker-compose file
cat > docker-compose.yml << EOF
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=${environment}
      - FLASK_DEBUG=false
      - DATABASE_URL=postgresql://${db_username}:${db_password}@${db_host}:5432/${db_name}
      - SECRET_KEY=\$(openssl rand -hex 32)
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
EOF

# For this demo, we'll use a simple Python script
# In a real deployment, you'd pull your code from Git or ECR
cat > requirements.txt << 'EOF'
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
psycopg2-binary==2.9.7
python-dotenv==1.0.0
Werkzeug==2.3.7
EOF

# Create a simple version of your app for demo
cat > app.py << 'EOF'
from flask import Flask, jsonify
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)

@app.route('/health')
def health():
    try:
        # Test database connection
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        conn.close()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat(),
            'environment': os.environ.get('FLASK_ENV', 'unknown')
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503

@app.route('/api/status')
def status():
    return jsonify({
        'status': 'running',
        'environment': os.environ.get('FLASK_ENV', 'unknown'),
        'timestamp': datetime.utcnow().isoformat()
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF

# Build and start the application
docker-compose up -d

# Install CloudWatch agent
yum install -y amazon-cloudwatch-agent

# Configure CloudWatch agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << EOF
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/messages",
            "log_group_name": "/aws/ec2/${environment}/system",
            "log_stream_name": "{instance_id}",
            "timezone": "UTC"
          }
        ]
      }
    }
  },
  "metrics": {
    "namespace": "TaskManager/${environment}",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          "cpu_usage_idle",
          "cpu_usage_iowait",
          "cpu_usage_user",
          "cpu_usage_system"
        ],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": [
          "used_percent"
        ],
        "metrics_collection_interval": 60,
        "resources": [
          "*"
        ]
      },
      "mem": {
        "measurement": [
          "mem_used_percent"
        ],
        "metrics_collection_interval": 60
      }
    }
  }
}
EOF

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s

# Create a log file to confirm the script ran
echo "User data script completed at $(date)" > /var/log/user-data.log
```

### Step 4: Update Your Dev Environment

**Update `terraform/environments/dev/main.tf` (add these modules):**

```hcl
# Add the ALB module
module "alb" {
  source = "../../modules/alb"

  environment           = var.environment
  vpc_id               = module.vpc.vpc_id
  public_subnet_ids    = module.vpc.public_subnet_ids
  alb_security_group_id = module.security_groups.alb_security_group_id
}

# Add the EC2 module
module "ec2" {
  source = "../../modules/ec2"

  environment           = var.environment
  instance_type        = var.instance_type
  key_name             = var.key_name
  private_subnet_ids   = module.vpc.private_subnet_ids
  web_security_group_id = module.security_groups.web_security_group_id
  target_group_arn     = module.alb.target_group_arn
  
  min_size             = var.min_size
  max_size             = var.max_size
  desired_capacity     = var.desired_capacity
  
  db_endpoint          = module.rds.db_endpoint
  db_name              = module.rds.db_name
  db_username          = "taskuser"
  db_password          = var.db_password
}
```

**Add to `terraform/environments/dev/variables.tf`:**

```hcl
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "EC2 Key Pair name (optional)"
  type        = string
  default     = null
}

variable "min_size" {
  description = "Minimum number of instances"
  type        = number
  default     = 1
}

variable "max_size" {
  description = "Maximum number of instances"
  type        = number
  default     = 3
}

variable "desired_capacity" {
  description = "Desired number of instances"
  type        = number
  default     = 1
}
```

**Add to `terraform/environments/dev/outputs.tf`:**

```hcl
output "alb_dns_name" {
  description = "Load balancer DNS name"
  value       = module.alb.alb_dns_name
}

output "application_url" {
  description = "Application URL"
  value       = "http://${module.alb.alb_dns_name}"
}
```

### Step 5: Deploy Your Complete Infrastructure

```bash
# Make sure you're in the dev environment directory
cd terraform/environments/dev

# Set the database password
export TF_VAR_db_password="MySecurePassword123!"

# Plan the deployment
terraform plan

# Apply the changes (this will take about 10-15 minutes)
terraform apply
```

### Step 6: Test Your Application

```bash
# Get the load balancer DNS name
ALB_DNS=$(terraform output -raw alb_dns_name)

# Test the health endpoint (might take a few minutes for instances to be ready)
curl "http://$ALB_DNS/health"

# Test the status endpoint
curl "http://$ALB_DNS/api/status"

# Visit in browser
echo "Visit: http://$ALB_DNS"
```

### Step 7: Verify Everything Works

1. **AWS Console Verification:**
   - EC2 → Load Balancers → You should see your ALB
   - EC2 → Auto Scaling Groups → You should see your ASG with 1 instance
   - EC2 → Instances → You should see 1 running instance

2. **Application Testing:**
   - Health check should return status "healthy"
   - Status endpoint should return environment info
   - Load balancer should distribute traffic

### 🎉 Lab 4 Complete!

**What did we just do?**
- Created an Application Load Balancer to distribute traffic
- Set up an Auto Scaling Group with EC2 instances
- Configured health checks and monitoring
- Deployed your application to the cloud

**Why is this important?**
- Your application is now highly available
- It can automatically scale based on demand
- Traffic is distributed across multiple servers
- Health checks ensure unhealthy instances are replaced

---

## 🚀 LAB 5: Automated CI/CD Pipeline (90 minutes)

### What is CI/CD?

CI/CD stands for Continuous Integration/Continuous Deployment. It automatically:
- Tests your code when you make changes
- Builds and packages your application
- Deploys it to different environments
- Runs tests to make sure everything works

### Step 1: Create Your GitHub Repository

```bash
# Initialize git in your project directory (if not already done)
git init

# Add all files
git add .

# Make your first commit
git commit -m "Initial commit: Task Manager application with infrastructure"

# Create a GitHub repository at https://github.com/new
# Name it something like "task-manager-devops"

# Add the remote repository
git remote add origin https://github.com/YOUR_USERNAME/task-manager-devops.git

# Push your code
git push -u origin main
```

### Step 2: Create an ECR Repository

ECR (Elastic Container Registry) is where we'll store our Docker images.

```bash
# Create ECR repository
aws ecr create-repository --repository-name taskmanager --region us-east-1

# Get login command
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Note: Replace YOUR_ACCOUNT_ID with your actual AWS account ID
```

> 🐳 **What is Amazon ECR?**
> - ECR (Elastic Container Registry) is AWS's Docker image storage service
> - It's like Docker Hub but private and integrated with AWS
> - Images stored here can be pulled by your EC2 instances
> - The login command authenticates Docker to push/pull images

### Step 3: Create Basic Tests

**Create `tests/test_app.py`:**

```python
import pytest
import json
import os
import sys

# Add the parent directory to the path so we can import our app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, User, Task, TaskStatus, TaskPriority

@pytest.fixture
def client():
    """Create a test client for our app"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_health_check(client):
    """Test that health check endpoint works"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_create_user(client):
    """Test creating a new user"""
    response = client.post('/api/users', 
                          json={
                              'username': 'testuser',
                              'email': 'test@example.com',
                              'password': 'password123'
                          })
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['username'] == 'testuser'
    assert data['email'] == 'test@example.com'

def test_get_users(client):
    """Test getting list of users"""
    response = client.get('/api/users')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'users' in data
    assert 'pagination' in data

def test_create_task(client):
    """Test creating a new task"""
    # First create a user
    user_response = client.post('/api/users', 
                               json={
                                   'username': 'testuser',
                                   'email': 'test@example.com',
                                   'password': 'password123'
                               })
    user_data = json.loads(user_response.data)
    
    # Then create a task
    response = client.post('/api/tasks',
                          json={
                              'title': 'Test Task',
                              'description': 'Test Description',
                              'user_id': user_data['id'],
                              'priority': 'high'
                          })
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['title'] == 'Test Task'
    assert data['priority'] == 'high'

def test_get_tasks(client):
    """Test getting list of tasks"""
    response = client.get('/api/tasks')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'tasks' in data
    assert 'pagination' in data

def test_dashboard_stats(client):
    """Test dashboard stats endpoint"""
    response = client.get('/api/dashboard-stats')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'total_users' in data
    assert 'total_tasks' in data
```

**Create `tests/__init__.py`:**

```python
# Empty file to make tests a package
```

**Create `tests/conftest.py`:**

```python
import os
import sys
import pytest

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment variables for testing
os.environ['FLASK_ENV'] = 'testing'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
```

### Step 4: Create GitHub Actions Workflow

**Create `.github/workflows/ci-cd.yml`:**

```yaml
name: CI/CD Pipeline for Task Manager

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: taskmanager

jobs:
  # Job 1: Run tests
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_USER: taskuser
          POSTGRES_PASSWORD: taskpass
          POSTGRES_DB: taskmanager
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

    - name: Cache pip packages
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      env:
        DATABASE_URL: postgresql://taskuser:taskpass@localhost:5432/taskmanager
        FLASK_ENV: testing
      run: |
        # Initialize database
        python init_db.py
        
        # Run tests with coverage
        python -m pytest tests/ -v --cov=. --cov-report=xml --cov-report=term-missing

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
        fail_ci_if_error: false

  # Job 2: Security scan
  security-scan:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'

    - name: Upload Trivy scan results to GitHub Security tab
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

  # Job 3: Build and push Docker image
  build:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'
    
    outputs:
      image-tag: ${{ steps.build-image.outputs.image-tag }}
      image-uri: ${{ steps.build-image.outputs.image-uri }}
    
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

    - name: Build, tag, and push image to Amazon ECR
      id: build-image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        # Build Docker image
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        
        # Push image to ECR
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        
        # Tag and push environment-specific tags
        if [[ $GITHUB_REF == 'refs/heads/main' ]]; then
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:prod
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:prod
        elif [[ $GITHUB_REF == 'refs/heads/develop' ]]; then
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:dev
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:dev
        fi
        
        # Set outputs
        echo "image-tag=$IMAGE_TAG" >> $GITHUB_OUTPUT
        echo "image-uri=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG" >> $GITHUB_OUTPUT

  # Job 4: Deploy to Development
  deploy-dev:
    needs: build
    runs-on: ubuntu-latest
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

    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v3
      with:
        terraform_version: 1.6.0

    - name: Deploy to Development Environment
      env:
        TF_VAR_db_password: ${{ secrets.DEV_DB_PASSWORD }}
        TF_VAR_image_tag: ${{ needs.build.outputs.image-tag }}
      run: |
        cd terraform/environments/dev
        terraform init
        terraform plan
        terraform apply -auto-approve
        
        # Get ALB DNS name for testing
        echo "ALB_DNS=$(terraform output -raw alb_dns_name)" >> $GITHUB_ENV

    - name: Wait for deployment to complete
      run: |
        echo "Waiting for deployment to complete..."
        sleep 60

    - name: Run smoke tests
      run: |
        # Test health endpoint
        for i in {1..10}; do
          if curl -f "http://$ALB_DNS/health"; then
            echo "Health check passed!"
            break
          fi
          echo "Attempt $i failed, retrying in 30 seconds..."
          sleep 30
        done
        
        # Test API endpoint
        curl -f "http://$ALB_DNS/api/dashboard-stats" || exit 1
        
        echo "✅ Development deployment successful!"
        echo "🌐 Application URL: http://$ALB_DNS"

  # Job 5: Deploy to Production
  deploy-prod:
    needs: build
    runs-on: ubuntu-latest
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

    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v3
      with:
        terraform_version: 1.6.0

    - name: Deploy to Production Environment
      env:
        TF_VAR_db_password: ${{ secrets.PROD_DB_PASSWORD }}
        TF_VAR_image_tag: ${{ needs.build.outputs.image-tag }}
      run: |
        cd terraform/environments/prod
        terraform init
        terraform plan
        terraform apply -auto-approve
        
        # Get ALB DNS name for testing
        echo "ALB_DNS=$(terraform output -raw alb_dns_name)" >> $GITHUB_ENV

    - name: Run production smoke tests
      run: |
        # Test health endpoint
        for i in {1..10}; do
          if curl -f "http://$ALB_DNS/health"; then
            echo "Production health check passed!"
            break
          fi
          echo "Attempt $i failed, retrying in 30 seconds..."
          sleep 30
        done
        
        echo "🚀 Production deployment successful!"
        echo "🌐 Production URL: http://$ALB_DNS"
```

### Step 5: Set Up GitHub Secrets

In your GitHub repository:

1. Go to **Settings** → **Secrets and Variables** → **Actions**
2. Click **New repository secret** and add:

   - `AWS_ACCESS_KEY_ID`: Your AWS access key
   - `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
   - `DEV_DB_PASSWORD`: Password for dev database
   - `PROD_DB_PASSWORD`: Password for production database

### Step 6: Create Production Environment

**Copy the dev environment:**

```bash
# Copy dev environment to create prod
cp -r terraform/environments/dev terraform/environments/prod

# Edit terraform/environments/prod/variables.tf
# Update defaults for production:
```

**Edit `terraform/environments/prod/variables.tf`:**

```hcl
variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small"  # Bigger instances for production
}

variable "min_size" {
  description = "Minimum number of instances"
  type        = number
  default     = 2  # More instances for production
}

variable "max_size" {
  description = "Maximum number of instances"
  type        = number
  default     = 6
}

variable "desired_capacity" {
  description = "Desired number of instances"
  type        = number
  default     = 2
}

variable "db_instance_class" {
  description = "Database instance size"
  type        = string
  default     = "db.t3.small"  # Bigger database for production
}

variable "allocated_storage" {
  description = "Initial database storage in GB"
  type        = number
  default     = 100
}

variable "backup_retention_period" {
  description = "Days to keep database backups"
  type        = number
  default     = 7  # Keep backups longer in production
}

# Keep all other variables the same as dev
```

### Step 7: Test Your CI/CD Pipeline

```bash
# Create a develop branch
git checkout -b develop

# Make a small change to test CI/CD
echo "# CI/CD Test" >> README.md

# Commit and push
git add .
git commit -m "Test CI/CD pipeline"
git push origin develop

# Go to GitHub and check the Actions tab
# You should see the workflow running
```

### Step 8: Create a Production Deploy

```bash
# Merge develop to main to trigger production deployment
git checkout main
git merge develop
git push origin main

# Check GitHub Actions for the production deployment
```

### 🎉 Lab 5 Complete!

**What did we just do?**
- Created automated tests for your application
- Set up a CI/CD pipeline with GitHub Actions
- Configured automatic deployments to dev and production
- Added security scanning and code coverage
- Created a complete DevOps workflow

**Why is this important?**
- Every code change is automatically tested
- Deployments are consistent and repeatable
- You catch bugs before they reach production
- Your team can deploy safely and frequently

---

## 📊 LAB 6: Monitoring and Alerting (45 minutes)

### What Are We Setting Up?

We'll create:
- **CloudWatch Alarms**: Monitor CPU, memory, and application metrics
- **SNS Notifications**: Get email alerts when things go wrong
- **CloudWatch Dashboard**: Visual overview of your system
- **Log Aggregation**: Collect logs from all your servers

### Step 1: Create the Monitoring Module

**Create `terraform/modules/monitoring/main.tf`:**

```hcl
# CloudWatch Log Group for application logs
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/aws/ec2/${var.environment}/app"
  retention_in_days = var.log_retention_days

  tags = {
    Environment = var.environment
    Project     = "TaskManager"
  }
}

# CloudWatch Log Group for system logs
resource "aws_cloudwatch_log_group" "system_logs" {
  name              = "/aws/ec2/${var.environment}/system"
  retention_in_days = var.log_retention_days

  tags = {
    Environment = var.environment
    Project     = "TaskManager"
  }
}

# SNS Topic for alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.environment}-alerts"

  tags = {
    Environment = var.environment
    Project     = "TaskManager"
  }
}

# Email subscription for alerts
resource "aws_sns_topic_subscription" "email_alerts" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch Alarm: High CPU Usage
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "${var.environment}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ec2 cpu utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    AutoScalingGroupName = var.asg_name
  }

  tags = {
    Environment = var.environment
    Project     = "TaskManager"
  }
}

# CloudWatch Alarm: Database High CPU
resource "aws_cloudwatch_metric_alarm" "database_cpu" {
  alarm_name          = "${var.environment}-database-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS cpu utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = var.db_instance_id
  }

  tags = {
    Environment = var.environment
    Project     = "TaskManager"
  }
}

# CloudWatch Alarm: High Response Time
resource "aws_cloudwatch_metric_alarm" "alb_response_time" {
  alarm_name          = "${var.environment}-alb-high-response-time"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Average"
  threshold           = "1"
  alarm_description   = "This metric monitors ALB response time"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  tags = {
    Environment = var.environment
    Project     = "TaskManager"
  }
}

# CloudWatch Alarm: High 5xx Error Rate
resource "aws_cloudwatch_metric_alarm" "alb_5xx_errors" {
  alarm_name          = "${var.environment}-alb-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HTTPCode_ELB_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors ALB 5xx errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  tags = {
    Environment = var.environment
    Project     = "TaskManager"
  }
}

# CloudWatch Alarm: Database Connection Failures
resource "aws_cloudwatch_metric_alarm" "database_connections" {
  alarm_name          = "${var.environment}-database-connection-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "50"
  alarm_description   = "This metric monitors RDS connection count"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = var.db_instance_id
  }

  tags = {
    Environment = var.environment
    Project     = "TaskManager"
  }
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.environment}-taskmanager-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/EC2", "CPUUtilization", "AutoScalingGroupName", var.asg_name],
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", var.db_instance_id],
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", var.alb_arn_suffix]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "System Performance"
          yAxis = {
            left = {
              min = 0
              max = 100
            }
          }
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", var.alb_arn_suffix],
            [".", "HTTPCode_ELB_5XX_Count", ".", "."],
            [".", "HTTPCode_ELB_4XX_Count", ".", "."],
            [".", "HTTPCode_Target_2XX_Count", ".", "."]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Request Metrics"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", var.db_instance_id],
            [".", "FreeStorageSpace", ".", "."],
            [".", "ReadLatency", ".", "."],
            [".", "WriteLatency", ".", "."]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Database Metrics"
        }
      }
    ]
  })
}
```

**Create `terraform/modules/monitoring/variables.tf`:**

```hcl
variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "alert_email" {
  description = "Email address for alerts"
  type        = string
  default     = ""
}

variable "asg_name" {
  description = "Auto Scaling Group name"
  type        = string
}

variable "db_instance_id" {
  description = "Database instance ID"
  type        = string
}

variable "alb_arn_suffix" {
  description = "ALB ARN suffix"
  type        = string
}

variable "log_retention_days" {
  description = "Log retention period in days"
  type        = number
  default     = 14
}
```

**Create `terraform/modules/monitoring/outputs.tf`:**

```hcl
output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = aws_sns_topic.alerts.arn
}

output "dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}
```

### Step 2: Update Your Dev Environment

**Update `terraform/environments/dev/main.tf` (add this module):**

```hcl
# Add the monitoring module
module "monitoring" {
  source = "../../modules/monitoring"

  environment        = var.environment
  aws_region         = var.aws_region
  alert_email        = var.alert_email
  asg_name           = module.ec2.asg_name
  db_instance_id     = module.rds.db_instance_id
  alb_arn_suffix     = module.alb.alb_arn_suffix
  log_retention_days = var.log_retention_days
}
```

**Add to `terraform/environments/dev/variables.tf`:**

```hcl
variable "alert_email" {
  description = "Email address for alerts"
  type        = string
  default     = ""
}

variable "log_retention_days" {
  description = "Log retention period in days"
  type        = number
  default     = 7
}
```

**Add to `terraform/environments/dev/outputs.tf`:**

```hcl
output "dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = module.monitoring.dashboard_url
}
```

### Step 3: Deploy Monitoring

```bash
# Navigate to dev environment
cd terraform/environments/dev

# Set your email for alerts
export TF_VAR_alert_email="your-email@example.com"
export TF_VAR_db_password="MySecurePassword123!"

# Plan and apply
terraform plan
terraform apply
```

### Step 4: Create Staging and Production Environments

**Create staging environment:**

```bash
# Copy dev to staging
cp -r terraform/environments/dev terraform/environments/staging

# Edit terraform/environments/staging/variables.tf
# Update the environment default to "staging"
```

**Create production environment:**

```bash
# Copy dev to prod (if not already done)
cp -r terraform/environments/dev terraform/environments/prod

# Edit terraform/environments/prod/variables.tf
# Update the environment default to "prod"
```

### Step 5: Test Your Monitoring

```bash
# Get your application URL
ALB_DNS=$(terraform output -raw alb_dns_name)

# Generate some load to trigger metrics
for i in {1..100}; do
  curl "http://$ALB_DNS/health" &
  curl "http://$ALB_DNS/api/dashboard-stats" &
done

# Wait for all requests to complete
wait

# Check CloudWatch metrics in AWS Console
echo "Check your CloudWatch dashboard: $(terraform output -raw dashboard_url)"
```

### Step 6: Set Up Email Notifications

1. **Check your email** for the SNS subscription confirmation
2. **Click "Confirm subscription"** in the email
3. **Test an alert** by generating high CPU usage

### Step 7: View Your Dashboard

```bash
# Get dashboard URL
terraform output dashboard_url

# Open in browser to see your metrics
```

### 🎉 Lab 6 Complete!

**What did we just do?**
- Created CloudWatch alarms for key metrics
- Set up email notifications for alerts
- Built a dashboard to visualize system health
- Configured log aggregation for troubleshooting

**Why is this important?**
- You'll know immediately when something goes wrong
- You can see trends and patterns in your system
- You can troubleshoot issues faster with centralized logs
- You can make data-driven decisions about scaling

---

## 🎯 FINAL TEST: End-to-End Validation (30 minutes)

### Let's Test Everything!

Now we'll verify that your complete system works end-to-end.

### Step 1: Deploy All Environments

```bash
# Deploy staging
cd terraform/environments/staging
export TF_VAR_db_password="StagingPassword123!"
export TF_VAR_alert_email="your-email@example.com"
terraform init
terraform plan
terraform apply

# Deploy production
cd ../prod
export TF_VAR_db_password="ProductionPassword123!"
export TF_VAR_alert_email="your-email@example.com"
terraform init
terraform plan
terraform apply
```

### Step 2: Test CI/CD Pipeline

```bash
# Create a feature branch
git checkout -b feature/monitoring-improvement

# Add a new endpoint to test
echo "
@api.route('/api/monitoring', methods=['GET'])
def get_monitoring():
    return jsonify({
        'status': 'operational',
        'environment': os.environ.get('FLASK_ENV', 'unknown'),
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }), 200
" >> routes.py

# Commit and push
git add .
git commit -m "Add monitoring endpoint"
git push origin feature/monitoring-improvement

# Create pull request on GitHub
# Merge to develop branch
# Watch CI/CD pipeline deploy to dev

# Merge develop to main
# Watch CI/CD pipeline deploy to production
```

### Step 3: Test All Environments

```bash
# Test development
cd terraform/environments/dev
DEV_URL=$(terraform output -raw application_url)
echo "Dev environment: $DEV_URL"
curl "$DEV_URL/health"
curl "$DEV_URL/api/monitoring"

# Test staging
cd ../staging
STAGING_URL=$(terraform output -raw application_url)
echo "Staging environment: $STAGING_URL"
curl "$STAGING_URL/health"
curl "$STAGING_URL/api/monitoring"

# Test production
cd ../prod
PROD_URL=$(terraform output -raw application_url)
echo "Production environment: $PROD_URL"
curl "$PROD_URL/health"
curl "$PROD_URL/api/monitoring"
```

### Step 4: Test Monitoring and Alerting

```bash
# Generate load to trigger monitoring
for env in dev staging prod; do
  cd "terraform/environments/$env"
  ALB_DNS=$(terraform output -raw alb_dns_name)
  
  echo "Testing $env environment..."
  
  # Generate load
  for i in {1..50}; do
    curl "http://$ALB_DNS/health" &
    curl "http://$ALB_DNS/api/dashboard-stats" &
  done
  
  wait
  echo "Load test complete for $env"
done
```

### Step 5: Verify Everything Works

**Check these items:**

✅ **Infrastructure**
- [ ] All 3 environments deployed (dev, staging, prod)
- [ ] Load balancers accessible
- [ ] Databases running and accessible
- [ ] Auto scaling groups have healthy instances

✅ **CI/CD Pipeline**
- [ ] Tests pass automatically
- [ ] Security scans complete
- [ ] Docker images build and push to ECR
- [ ] Deployments trigger on branch changes

✅ **Monitoring**
- [ ] CloudWatch metrics showing data
- [ ] Alarms configured and functional
- [ ] Email notifications working
- [ ] Dashboard displays system health

✅ **Application**
- [ ] Health checks return 200
- [ ] API endpoints work
- [ ] Database connections successful
- [ ] Web interface accessible

### Step 6: Cost Cleanup (Important!)

```bash
# When you're done testing, destroy resources to avoid charges
cd terraform/environments/dev
terraform destroy

cd ../staging
terraform destroy

cd ../prod
terraform destroy
```

> 💰 **Cost Management Tips:**
> - Always run `terraform destroy` when done with testing
> - Use `terraform plan -destroy` to preview what will be deleted
> - Monitor your AWS billing dashboard regularly
> - Set up billing alerts in AWS
> - Consider using AWS Cost Explorer to analyze spending patterns
> - Most resources incur charges even when not actively used

## 🎉 Congratulations! You've Completed the Lab!

### What You've Accomplished

🚀 **You built a complete DevOps pipeline from scratch!**

✅ **Infrastructure as Code**: Created reusable Terraform modules
✅ **Multi-Environment Setup**: Dev, Staging, and Production environments
✅ **Containerization**: Dockerized your Flask application
✅ **CI/CD Pipeline**: Automated testing, building, and deployment
✅ **Monitoring & Alerting**: CloudWatch metrics, alarms, and dashboards
✅ **Security**: Proper IAM roles, security groups, and secret management
✅ **High Availability**: Load balancers, auto scaling, and multi-AZ deployment

### Key Skills You've Learned

- **Docker** containerization and orchestration
- **Terraform** infrastructure as code
- **AWS** cloud services (VPC, EC2, RDS, ALB, CloudWatch)
- **GitHub Actions** CI/CD pipelines
- **PostgreSQL** database management
- **System monitoring** and alerting
- **DevOps best practices** and workflows

### What's Next?

Now that you have a solid foundation, you can:

1. **Add SSL/TLS** with AWS Certificate Manager
2. **Implement Blue-Green Deployment** for zero-downtime updates
3. **Add Kubernetes** with Amazon EKS
4. **Set up Log Analysis** with Elasticsearch
5. **Add Performance Monitoring** with APM tools
6. **Implement Disaster Recovery** across regions

### Real-World Applications

This setup is production-ready and follows industry best practices. You can use this pattern for:
- Web applications
- APIs and microservices
- E-commerce platforms
- SaaS applications
- Enterprise software

### Keep Learning!

- Practice with different AWS services
- Explore Kubernetes and container orchestration
- Learn about service mesh with Istio
- Study site reliability engineering (SRE)
- Contribute to open-source DevOps projects

**You're now ready to be a DevOps engineer!** 🚀

---

*Remember: Always clean up your AWS resources when you're done to avoid unnecessary charges.*