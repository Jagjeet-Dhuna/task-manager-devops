# Multi-Environment Web App Deployment: Advanced Lab Guide

## 🎯 Lab Objectives

This is an advanced, instruction-based lab for experienced developers who want to quickly implement a production-ready multi-environment deployment system. You should be comfortable with:
- Docker and containerization concepts
- Basic AWS services and CLI
- Terraform fundamentals
- Git workflows and CI/CD concepts

**Estimated Time:** 4-6 hours for experienced practitioners

---

## 📋 Prerequisites

### Required Tools (Install Before Starting)
- [ ] **AWS CLI** - [Download](https://aws.amazon.com/cli/)
- [ ] **Terraform** - [Download](https://terraform.io/downloads)
- [ ] **Docker Desktop** - [Download](https://docker.com/products/docker-desktop)
- [ ] **Git** - [Download](https://git-scm.com/)
- [ ] **VS Code** (recommended) - [Download](https://code.visualstudio.com/)

### Required Accounts
- [ ] **AWS Account** - [Sign up](https://aws.amazon.com/free/)
- [ ] **GitHub Account** - [Sign up](https://github.com/)

### Verify Prerequisites
```bash
# Check installed tools
aws --version
terraform --version
docker --version
git --version
```

---

## 🚀 LAB 1: Application Containerization (30 minutes)

### Objectives
- Create production-ready Docker configuration
- Implement multi-stage builds for optimization
- Set up development environment with Docker Compose

### Implementation Steps

1. **Create optimized Dockerfile** with multi-stage build, security hardening, and health checks
2. **Configure docker-compose.yml** for local development with PostgreSQL
3. **Implement .dockerignore** to exclude unnecessary files
4. **Test containerized application** with database connectivity

### Key Requirements

**Dockerfile Configuration:**
```dockerfile
# Multi-stage build for smaller image size
FROM python:3.9-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1
CMD ["python", "app.py"]
```

**Create `docker-compose.yml` in project root:**
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
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: postgres:13-alpine
    environment:
      - POSTGRES_USER=taskuser
      - POSTGRES_PASSWORD=taskpass
      - POSTGRES_DB=taskmanager
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init_db.sql:/docker-entrypoint-initdb.d/init_db.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U taskuser -d taskmanager"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
```

**Create `.dockerignore` file:**
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
```

### Validation Commands

```bash
# Build and test containers
docker-compose up --build -d  # -d runs in detached mode (background)
curl http://localhost:5000/health
curl http://localhost:5000/api/users
docker-compose down

# Verify image optimization
docker images | grep taskmanager  # Check image size after multi-stage build
```

> 📊 **Performance Tips:**
> - Multi-stage builds can reduce image size by 50-70%
> - Use `.dockerignore` to exclude unnecessary files
> - Pin specific versions in requirements.txt for reproducible builds
> - Consider using Alpine Linux base images for smaller footprint

### Success Criteria
- ✅ Multi-stage build reduces image size by >30%
- ✅ Health checks pass consistently
- ✅ Database connectivity verified
- ✅ Non-root user implementation
- ✅ Proper resource cleanup on container stop

---

## 🏗️ LAB 2: Infrastructure Foundation with Terraform (45 minutes)

### Objectives
- Design reusable Terraform module architecture
- Implement network security best practices
- Create environment-specific configurations
- Establish state management strategy

### Architecture Overview

```
terraform/
├── modules/                    # Reusable infrastructure components
│   ├── vpc/                   # Network foundation
│   ├── security-groups/       # Security rules
│   ├── ec2/                   # Compute resources
│   ├── rds/                   # Database layer
│   ├── alb/                   # Load balancing
│   └── monitoring/            # Observability
├── environments/              # Environment-specific configs
│   ├── dev/                   # Development environment
│   ├── staging/               # Staging environment
│   └── prod/                  # Production environment
└── global/                    # Shared resources
```

### Implementation Requirements

1. **Create modular VPC** with public/private subnets across AZs
2. **Implement security groups** with least-privilege access
3. **Configure environment-specific variables** for scaling
4. **Set up remote state management** with S3 backend (optional)

### Step 2.2: Create VPC Module

**Create `terraform/modules/vpc/main.tf`:**
```hcl
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

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "${var.environment}-igw"
    Environment = var.environment
    Project     = "TaskManager"
  }
}

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

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

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

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

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

resource "aws_eip" "nat" {
  count  = length(aws_subnet.public)
  domain = "vpc"

  tags = {
    Name        = "${var.environment}-nat-eip-${count.index + 1}"
    Environment = var.environment
    Project     = "TaskManager"
  }
}

resource "aws_route_table" "private" {
  count  = length(aws_subnet.private)
  vpc_id = aws_vpc.main.id

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

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}
```

**Create `terraform/modules/vpc/variables.tf`:**
```hcl
variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}
```

**Create `terraform/modules/vpc/outputs.tf`:**
```hcl
output "vpc_id" {
  description = "ID of the VPC"
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
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}
```

### Step 2.3: Create Security Groups Module

**Create `terraform/modules/security-groups/main.tf`:**
```hcl
# ALB Security Group
resource "aws_security_group" "alb" {
  name        = "${var.environment}-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

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

# Web Server Security Group
resource "aws_security_group" "web" {
  name        = "${var.environment}-web-sg"
  description = "Security group for web servers"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Application Port"
    from_port       = 5000
    to_port         = 5000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr_block]
  }

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

# Database Security Group
resource "aws_security_group" "db" {
  name        = "${var.environment}-db-sg"
  description = "Security group for database"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL"
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
  description = "VPC ID"
  type        = string
}

variable "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  type        = string
}
```

**Create `terraform/modules/security-groups/outputs.tf`:**
```hcl
output "alb_security_group_id" {
  description = "Security group ID for ALB"
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

### Step 2.4: Create Development Environment

**Create `terraform/environments/dev/main.tf`:**
```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC Module
module "vpc" {
  source = "../../modules/vpc"

  environment            = var.environment
  vpc_cidr              = var.vpc_cidr
  public_subnet_cidrs   = var.public_subnet_cidrs
  private_subnet_cidrs  = var.private_subnet_cidrs
  availability_zones    = var.availability_zones
}

# Security Groups Module
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
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}
```

**Create `terraform/environments/dev/outputs.tf`:**
```hcl
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnet_ids
}
```

### Key Module Features

**VPC Module Requirements:**
- Multi-AZ deployment for high availability
- Public subnets for load balancers
- Private subnets for application servers
- NAT Gateway for outbound internet access
- Route tables with proper traffic routing

**Security Groups Module:**
- Principle of least privilege
- Environment-specific rules
- Proper ingress/egress configuration
- Security group references (not CIDR blocks)

### Deployment Instructions

```bash
# Environment setup
cd terraform/environments/dev
terraform init       # Initialize backend and download providers
terraform validate   # Check syntax and configuration
terraform plan      # Preview changes (dry run)
terraform apply     # Apply changes to infrastructure

# Verify deployment
aws ec2 describe-vpcs --filters "Name=tag:Environment,Values=dev"
```

> 🔧 **Terraform Best Practices:**
> - Use `terraform fmt` to format code consistently
> - Enable remote state with S3 backend for team collaboration
> - Use `terraform workspace` for environment isolation
> - Always review `terraform plan` output before applying
> - Use `terraform graph` to visualize resource dependencies

### Success Criteria
- ✅ VPC created with proper CIDR allocation
- ✅ Subnets distributed across availability zones
- ✅ Internet and NAT gateways configured
- ✅ Security groups follow least-privilege principle
- ✅ All resources properly tagged

---

## 🗄️ LAB 3: Database Infrastructure (30 minutes)

### Step 3.1: Create RDS Module

**Create `terraform/modules/rds/main.tf`:**
```hcl
resource "aws_db_subnet_group" "main" {
  name       = "${var.environment}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "${var.environment}-db-subnet-group"
    Environment = var.environment
    Project     = "TaskManager"
  }
}

resource "aws_db_parameter_group" "main" {
  family = "postgres13"
  name   = "${var.environment}-db-params"

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

resource "aws_db_instance" "main" {
  identifier = "${var.environment}-taskmanager-db"
  
  # Engine configuration
  engine         = "postgres"
  engine_version = "13.13"
  instance_class = var.db_instance_class
  
  # Storage configuration
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type         = "gp2"
  storage_encrypted    = true
  
  # Database configuration
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  
  # Network configuration
  vpc_security_group_ids = [var.db_security_group_id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  publicly_accessible    = false
  
  # Backup configuration
  backup_retention_period   = var.backup_retention_period
  backup_window            = var.backup_window
  maintenance_window       = var.maintenance_window
  delete_automated_backups = var.environment == "dev"
  
  # Parameter group
  parameter_group_name = aws_db_parameter_group.main.name
  
  # Snapshot configuration
  skip_final_snapshot       = var.environment == "dev"
  final_snapshot_identifier = var.environment != "dev" ? "${var.environment}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null
  
  # Monitoring
  monitoring_interval = var.monitoring_interval
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  
  # Security
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
  description = "Private subnet IDs for DB subnet group"
  type        = list(string)
}

variable "db_security_group_id" {
  description = "Security group ID for database"
  type        = string
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "Initial storage allocation"
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Maximum storage allocation"
  type        = number
  default     = 100
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "taskmanager"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "taskuser"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

variable "backup_window" {
  description = "Preferred backup window"
  type        = string
  default     = "07:00-09:00"
}

variable "maintenance_window" {
  description = "Preferred maintenance window"
  type        = string
  default     = "sun:05:00-sun:07:00"
}

variable "monitoring_interval" {
  description = "Enhanced monitoring interval"
  type        = number
  default     = 60
}
```

**Create `terraform/modules/rds/outputs.tf`:**
```hcl
output "db_endpoint" {
  description = "Database endpoint"
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

### Step 3.2: Update Dev Environment with RDS

**Update `terraform/environments/dev/main.tf`:**
```hcl
# Add to existing configuration
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
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "Initial storage allocation"
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Maximum storage allocation"
  type        = number
  default     = 50
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 1
}
```

### Step 3.3: Deploy Database Infrastructure

```bash
# Navigate to dev environment
cd terraform/environments/dev

# Set database password
export TF_VAR_db_password="YourSecurePassword123!"

# Plan and apply
terraform plan
terraform apply
```

### ✅ Lab 3 Checkpoint
- [ ] RDS instance created successfully
- [ ] Database is in private subnets
- [ ] Security groups allow web server access
- [ ] Database endpoint is accessible from VPC

---

## 🖥️ LAB 4: Application Load Balancer and EC2 (45 minutes)

### Step 4.1: Create ALB Module

**Create `terraform/modules/alb/main.tf`:**
```hcl
resource "aws_lb" "main" {
  name               = "${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_security_group_id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = var.environment == "prod"

  tags = {
    Name        = "${var.environment}-alb"
    Environment = var.environment
    Project     = "TaskManager"
  }
}

resource "aws_lb_target_group" "web" {
  name     = "${var.environment}-web-tg"
  port     = 5000
  protocol = "HTTP"
  vpc_id   = var.vpc_id

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

**Create `terraform/modules/alb/variables.tf` and `terraform/modules/alb/outputs.tf`:**
```hcl
# variables.tf
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

# outputs.tf
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
```

### Step 4.2: Create EC2 Module

**Create `terraform/modules/ec2/main.tf`:**
```hcl
# Get latest Amazon Linux 2 AMI
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

# IAM role for EC2 instances
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
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.environment}-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

# Launch template
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

# Auto Scaling Group
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

**Create `terraform/modules/ec2/user_data.sh`:**
```bash
#!/bin/bash
yum update -y
yum install -y docker git

# Start Docker service
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create application directory
mkdir -p /app
cd /app

# Clone application (you'll need to update this with your actual repo)
git clone https://github.com/yourusername/task-manager.git .

# Create environment file
cat > .env << EOF
FLASK_ENV=${environment}
FLASK_DEBUG=false
DATABASE_URL=postgresql://${db_username}:${db_password}@${db_host}:5432/${db_name}
SECRET_KEY=$(openssl rand -hex 32)
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
            "file_path": "/app/logs/taskmanager.log",
            "log_group_name": "/aws/ec2/${environment}/app",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
EOF

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s
```

### Step 4.3: Update Dev Environment with EC2 and ALB

**Update `terraform/environments/dev/main.tf`:**
```hcl
# Add to existing configuration
module "alb" {
  source = "../../modules/alb"

  environment           = var.environment
  vpc_id               = module.vpc.vpc_id
  public_subnet_ids    = module.vpc.public_subnet_ids
  alb_security_group_id = module.security_groups.alb_security_group_id
}

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
  description = "EC2 Key Pair name"
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

### Step 4.4: Deploy Complete Infrastructure

```bash
# Navigate to dev environment
cd terraform/environments/dev

# Plan and apply
terraform plan
terraform apply
```

### ✅ Lab 4 Checkpoint
- [ ] ALB created and accessible
- [ ] EC2 instances launched in Auto Scaling Group
- [ ] Application accessible via ALB DNS name
- [ ] Health checks passing

---

## 🚀 LAB 5: CI/CD Pipeline with GitHub Actions (45 minutes)

### Step 5.1: Create GitHub Repository

```bash
# Initialize git repository (if not already done)
git init
git add .
git commit -m "Initial commit"

# Create GitHub repository and push
git remote add origin https://github.com/yourusername/task-manager.git
git push -u origin main
```

### Step 5.2: Create ECR Repository

```bash
# Create ECR repository
aws ecr create-repository --repository-name taskmanager --region us-east-1
```

### Step 5.3: Create GitHub Actions Workflow

**Create `.github/workflows/ci-cd.yml`:**
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: taskmanager

jobs:
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
        python init_db.py
        python -m pytest tests/ -v --cov=. --cov-report=xml

    - name: Upload coverage to Codecov
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

  build:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'
    
    outputs:
      image-tag: ${{ steps.build-image.outputs.image-tag }}
    
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
        # Build and push image
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        
        # Also tag as latest for the environment
        if [[ $GITHUB_REF == 'refs/heads/main' ]]; then
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:prod
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:prod
        elif [[ $GITHUB_REF == 'refs/heads/develop' ]]; then
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:dev
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:dev
        fi
        
        echo "image-tag=$IMAGE_TAG" >> $GITHUB_OUTPUT

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
        terraform_version: 1.5.0

    - name: Deploy to Dev Environment
      env:
        TF_VAR_db_password: ${{ secrets.DEV_DB_PASSWORD }}
        TF_VAR_image_tag: ${{ needs.build.outputs.image-tag }}
      run: |
        cd terraform/environments/dev
        terraform init
        terraform plan
        terraform apply -auto-approve

    - name: Run smoke tests
      run: |
        # Wait for deployment to complete
        sleep 60
        
        # Get ALB DNS name
        ALB_DNS=$(terraform output -raw alb_dns_name)
        
        # Test health endpoint
        curl -f "http://$ALB_DNS/health" || exit 1
        
        # Test API endpoint
        curl -f "http://$ALB_DNS/api/users" || exit 1
        
        echo "Smoke tests passed!"

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
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

    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v3
      with:
        terraform_version: 1.5.0

    - name: Deploy to Staging Environment
      env:
        TF_VAR_db_password: ${{ secrets.STAGING_DB_PASSWORD }}
        TF_VAR_image_tag: ${{ needs.build.outputs.image-tag }}
      run: |
        cd terraform/environments/staging
        terraform init
        terraform plan
        terraform apply -auto-approve

  deploy-prod:
    needs: [build, deploy-staging]
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
        terraform_version: 1.5.0

    - name: Deploy to Production Environment
      env:
        TF_VAR_db_password: ${{ secrets.PROD_DB_PASSWORD }}
        TF_VAR_image_tag: ${{ needs.build.outputs.image-tag }}
      run: |
        cd terraform/environments/prod
        terraform init
        terraform plan
        terraform apply -auto-approve
```

### Step 5.4: Create Basic Tests

**Create `tests/test_app.py`:**
```python
import pytest
import json
from app import create_app
from models import db, User, Task, TaskStatus, TaskPriority

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_create_user(client):
    """Test user creation"""
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

def test_create_task(client):
    """Test task creation"""
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

def test_get_users(client):
    """Test getting users"""
    response = client.get('/api/users')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'users' in data
    assert 'pagination' in data
```

**Create `tests/__init__.py`:**
```python
# Empty file to make tests a package
```

### Step 5.5: Setup GitHub Secrets

In your GitHub repository, go to Settings → Secrets and Variables → Actions, and add:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `DEV_DB_PASSWORD`
- `STAGING_DB_PASSWORD`
- `PROD_DB_PASSWORD`

### Step 5.6: Test CI/CD Pipeline

```bash
# Create develop branch
git checkout -b develop

# Make a small change and push
echo "# Test CI/CD" >> README.md
git add .
git commit -m "Test CI/CD pipeline"
git push origin develop

# Check GitHub Actions tab for pipeline execution
```

> 🔄 **CI/CD Pipeline Flow:**
> - `develop` branch → triggers development deployment
> - `main` branch → triggers production deployment
> - Pull requests → run tests and security scans only
> - Each environment has isolated infrastructure and databases
> - Failed tests or security issues block deployment automatically

### ✅ Lab 5 Checkpoint
- [ ] GitHub Actions workflow runs successfully
- [ ] Tests pass in CI environment
- [ ] Docker image builds and pushes to ECR
- [ ] Application deploys to dev environment
- [ ] Smoke tests pass

---

## 📊 LAB 6: Monitoring and Alerting (30 minutes)

### Step 6.1: Create Monitoring Module

**Create `terraform/modules/monitoring/main.tf`:**
```hcl
# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/aws/ec2/${var.environment}/app"
  retention_in_days = var.log_retention_days

  tags = {
    Environment = var.environment
    Project     = "TaskManager"
  }
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.environment}-alerts"

  tags = {
    Environment = var.environment
    Project     = "TaskManager"
  }
}

resource "aws_sns_topic_subscription" "email_alerts" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch Alarms
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

  dimensions = {
    AutoScalingGroupName = var.asg_name
  }

  tags = {
    Environment = var.environment
    Project     = "TaskManager"
  }
}

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

  dimensions = {
    DBInstanceIdentifier = var.db_instance_id
  }

  tags = {
    Environment = var.environment
    Project     = "TaskManager"
  }
}

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

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  tags = {
    Environment = var.environment
    Project     = "TaskManager"
  }
}

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

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
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
          title  = "System Metrics"
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
            [".", "HTTPCode_ELB_4XX_Count", ".", "."]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Request Metrics"
        }
      }
    ]
  })
}
```

### Step 6.2: Update Environment with Monitoring

**Update `terraform/environments/dev/main.tf`:**
```hcl
# Add to existing configuration
module "monitoring" {
  source = "../../modules/monitoring"

  environment      = var.environment
  aws_region       = var.aws_region
  alert_email      = var.alert_email
  asg_name         = module.ec2.asg_name
  db_instance_id   = module.rds.db_instance_id
  alb_arn_suffix   = module.alb.alb_arn_suffix
  log_retention_days = 7
}
```

### Step 6.3: Create Production and Staging Environments

**Create `terraform/environments/staging/` and `terraform/environments/prod/`:**

Copy the dev environment files and modify the variables:

**For staging (`terraform/environments/staging/staging.tfvars`):**
```hcl
aws_region = "us-east-1"
environment = "staging"
instance_type = "t3.small"
min_size = 1
max_size = 4
desired_capacity = 2
db_instance_class = "db.t3.small"
allocated_storage = 50
max_allocated_storage = 100
backup_retention_period = 3
```

**For production (`terraform/environments/prod/prod.tfvars`):**
```hcl
aws_region = "us-east-1"
environment = "prod"
instance_type = "t3.medium"
min_size = 2
max_size = 6
desired_capacity = 2
db_instance_class = "db.t3.medium"
allocated_storage = 100
max_allocated_storage = 200
backup_retention_period = 7
```

### ✅ Lab 6 Checkpoint
- [ ] CloudWatch alarms created
- [ ] SNS notifications configured
- [ ] Dashboard shows system metrics
- [ ] Staging and production environments ready

---

## 🎯 FINAL LAB: End-to-End Testing (30 minutes)

### Step 7.1: Deploy All Environments

```bash
# Deploy staging
cd terraform/environments/staging
terraform init
terraform plan -var-file="staging.tfvars"
terraform apply -var-file="staging.tfvars"

# Deploy production
cd ../prod
terraform init
terraform plan -var-file="prod.tfvars"
terraform apply -var-file="prod.tfvars"
```

### Step 7.2: Test Complete CI/CD Pipeline

```bash
# Create feature branch
git checkout -b feature/new-endpoint

# Add a new endpoint to routes.py
echo "
@api.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        'status': 'running',
        'environment': os.environ.get('FLASK_ENV', 'unknown'),
        'timestamp': datetime.utcnow().isoformat()
    }), 200
" >> routes.py

# Commit and push to trigger CI/CD
git add .
git commit -m "Add status endpoint"
git push origin feature/new-endpoint

# Create pull request and merge to develop
# This should trigger deployment to dev

# Merge develop to main
# This should trigger deployment to staging and production
```

### Step 7.3: Verify Deployments

```bash
# Get ALB DNS names for each environment
cd terraform/environments/dev
DEV_ALB=$(terraform output -raw alb_dns_name)

cd ../staging
STAGING_ALB=$(terraform output -raw alb_dns_name)

cd ../prod
PROD_ALB=$(terraform output -raw alb_dns_name)

# Test each environment
echo "Testing Dev Environment:"
curl "http://$DEV_ALB/health"
curl "http://$DEV_ALB/api/status"

echo "Testing Staging Environment:"
curl "http://$STAGING_ALB/health"
curl "http://$STAGING_ALB/api/status"

echo "Testing Production Environment:"
curl "http://$PROD_ALB/health"
curl "http://$PROD_ALB/api/status"
```

### Step 7.4: Test Monitoring and Alerting

```bash
# Generate some load to trigger alerts
for i in {1..100}; do
  curl "http://$DEV_ALB/api/users" &
done

# Check CloudWatch metrics and alarms
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name RequestCount \
  --dimensions Name=LoadBalancer,Value=$DEV_ALB \
  --statistics Sum \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T01:00:00Z \
  --period 300
```

### ✅ Final Lab Checkpoint
- [ ] All environments deployed successfully
- [ ] CI/CD pipeline works end-to-end
- [ ] Applications accessible in all environments
- [ ] Monitoring shows metrics for all environments
- [ ] Alerts trigger when thresholds are exceeded

---

## 🎉 Lab Complete!

### What You've Accomplished

✅ **Containerized Application**: Dockerized Flask app with PostgreSQL
✅ **Infrastructure as Code**: Terraform modules for VPC, RDS, EC2, ALB
✅ **Multi-Environment Setup**: Dev, Staging, and Production environments
✅ **CI/CD Pipeline**: Automated testing, building, and deployment
✅ **Monitoring & Alerting**: CloudWatch metrics, alarms, and dashboards
✅ **Security Best Practices**: IAM roles, security groups, encrypted storage

### Next Steps

1. **Add SSL/TLS**: Implement HTTPS with ACM certificates
2. **Database Migrations**: Add automated database migration scripts
3. **Blue-Green Deployment**: Implement zero-downtime deployments
4. **Auto Scaling**: Configure dynamic scaling based on metrics
5. **Backup Strategy**: Implement automated backups and recovery procedures
6. **Cost Optimization**: Add cost monitoring and optimization strategies

### Troubleshooting Tips

- **Terraform State Issues**: Use `terraform state list` and `terraform import`
- **Application Issues**: Check CloudWatch logs and EC2 user data logs
- **Network Issues**: Verify security groups and route tables
- **Database Issues**: Check RDS parameter groups and security groups
- **CI/CD Issues**: Review GitHub Actions logs and AWS permissions

### Cost Management

Remember to destroy resources when not needed:

```bash
# Destroy all environments
cd terraform/environments/dev && terraform destroy
cd terraform/environments/staging && terraform destroy
cd terraform/environments/prod && terraform destroy
```

**Congratulations! You've successfully completed the Multi-Environment Web App Deployment lab!**