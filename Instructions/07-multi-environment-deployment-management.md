# Lab 07: Multi-Environment Deployment and Management

## Overview

In this final lab, you will deploy and manage multiple environments (staging and production) using infrastructure as code, implement environment promotion workflows, set up cross-environment monitoring, and create disaster recovery procedures. This lab completes your multi-environment deployment architecture.

## Objectives

After completing this lab, you will be able to:
- Deploy and configure staging and production environments
- Implement environment promotion workflows and approval processes
- Set up cross-environment monitoring and comparison
- Create disaster recovery and rollback procedures
- Implement environment lifecycle management

## Prerequisites

- Completed Lab 06 (Monitoring, Logging, and Alerting)
- Understanding of multi-environment deployment strategies
- Basic knowledge of disaster recovery concepts
- Existing development environment fully configured

## Duration

**Estimated Time:** 45 minutes

---

## Exercise 1: Create Environment-Specific Configurations

### Task 1: Create Staging Environment Configuration

1. **Create staging environment directory:**
   ```bash
   mkdir -p terraform/environments/staging
   cd terraform/environments/staging
   ```

2. **Create `terraform/environments/staging/main.tf`:**
   ```hcl
   # Staging Environment Configuration
   terraform {
     required_version = ">= 1.0"
     
     backend "s3" {
       bucket = "taskmanager-terraform-state-staging"
       key    = "staging/terraform.tfstate"
       region = "us-east-1"
       
       dynamodb_table = "taskmanager-terraform-locks"
       encrypt        = true
     }
     
     required_providers {
       aws = {
         source  = "hashicorp/aws"
         version = "~> 5.0"
       }
     }
   }
   
   provider "aws" {
     region = var.aws_region
     
     default_tags {
       tags = {
         Environment = "staging"
         Project     = var.project_name
         ManagedBy   = "terraform"
         Owner       = "devops-team"
       }
     }
   }
   
   # VPC Configuration
   module "vpc" {
     source = "../../modules/vpc"
   
     project_name = var.project_name
     environment  = var.environment
     vpc_cidr     = var.vpc_cidr
   
     public_subnet_cidrs   = var.public_subnet_cidrs
     private_subnet_cidrs  = var.private_subnet_cidrs
     database_subnet_cidrs = var.database_subnet_cidrs
   
     availability_zones = var.availability_zones
   }
   
   # Security Groups
   module "security_groups" {
     source = "../../modules/security-groups"
   
     project_name = var.project_name
     environment  = var.environment
     vpc_id       = module.vpc.vpc_id
   }
   
   # Database secrets
   module "secrets" {
     source = "../../modules/secrets"
   
     project_name      = var.project_name
     environment       = var.environment
     database_username = var.database_username
   }
   
   # Database instance
   module "database" {
     source = "../../modules/rds"
   
     project_name       = var.project_name
     environment        = var.environment
     database_subnets   = module.vpc.database_subnet_ids
     security_group_ids = [module.security_groups.database_security_group_id]
   
     instance_class          = var.db_instance_class
     allocated_storage       = var.db_allocated_storage
     max_allocated_storage   = var.db_max_allocated_storage
     database_name           = var.database_name
     database_username       = var.database_username
     database_password       = module.secrets.db_password
   
     backup_retention_period = var.db_backup_retention_period
     deletion_protection     = var.db_deletion_protection
     skip_final_snapshot     = var.db_skip_final_snapshot
   }
   
   # ECR Repository
   module "ecr" {
     source = "../../modules/ecr"
   
     project_name = var.project_name
     environment  = var.environment
   }
   
   # Application Load Balancer
   module "alb" {
     source = "../../modules/alb"
   
     project_name       = var.project_name
     environment        = var.environment
     vpc_id             = module.vpc.vpc_id
     public_subnet_ids  = module.vpc.public_subnet_ids
     security_group_ids = [module.security_groups.alb_security_group_id]
   
     enable_deletion_protection = var.alb_deletion_protection
     certificate_arn           = var.ssl_certificate_arn
   }
   
   # EC2 Auto Scaling Group
   module "ec2" {
     source = "../../modules/ec2"
   
     project_name        = var.project_name
     environment         = var.environment
     vpc_id              = module.vpc.vpc_id
     private_subnet_ids  = module.vpc.private_subnet_ids
     security_group_ids  = [module.security_groups.web_security_group_id]
     target_group_arn    = module.alb.target_group_arn
   
     ami_id              = data.aws_ami.amazon_linux.id
     instance_type       = var.ec2_instance_type
     key_name            = var.key_name
     min_size            = var.asg_min_size
     max_size            = var.asg_max_size
     desired_capacity    = var.asg_desired_capacity
   
     db_secret_arn       = module.secrets.db_secret_arn
     ecr_repository_url  = module.ecr.repository_url
   }
   
   # Monitoring
   module "monitoring" {
     source = "../../modules/monitoring"
   
     project_name    = var.project_name
     environment     = var.environment
     aws_region      = var.aws_region
     alb_name        = module.alb.alb_arn
     asg_name        = module.ec2.autoscaling_group_name
     db_instance_id  = module.database.db_instance_id
     target_group_name = module.alb.target_group_arn
   
     log_retention_days      = var.log_retention_days
     alert_email_addresses   = var.alert_email_addresses
     slack_webhook_url       = var.slack_webhook_url
     pagerduty_endpoint      = var.pagerduty_endpoint
     alert_phone_numbers     = var.alert_phone_numbers
   }
   
   # Data source for latest Amazon Linux AMI
   data "aws_ami" "amazon_linux" {
     most_recent = true
     owners      = ["amazon"]
   
     filter {
       name   = "name"
       values = ["amzn2-ami-hvm-*-x86_64-gp2"]
     }
   }
   ```

3. **Create `terraform/environments/staging/variables.tf`:**
   ```hcl
   # General Configuration
   variable "project_name" {
     description = "Name of the project"
     type        = string
     default     = "taskmanager"
   }
   
   variable "environment" {
     description = "Environment name"
     type        = string
     default     = "staging"
   }
   
   variable "aws_region" {
     description = "AWS region"
     type        = string
     default     = "us-east-1"
   }
   
   # VPC Configuration
   variable "vpc_cidr" {
     description = "CIDR block for VPC"
     type        = string
     default     = "10.1.0.0/16"
   }
   
   variable "public_subnet_cidrs" {
     description = "CIDR blocks for public subnets"
     type        = list(string)
     default     = ["10.1.1.0/24", "10.1.2.0/24"]
   }
   
   variable "private_subnet_cidrs" {
     description = "CIDR blocks for private subnets"
     type        = list(string)
     default     = ["10.1.3.0/24", "10.1.4.0/24"]
   }
   
   variable "database_subnet_cidrs" {
     description = "CIDR blocks for database subnets"
     type        = list(string)
     default     = ["10.1.5.0/24", "10.1.6.0/24"]
   }
   
   variable "availability_zones" {
     description = "List of availability zones"
     type        = list(string)
     default     = ["us-east-1a", "us-east-1b"]
   }
   
   # Database Configuration
   variable "db_instance_class" {
     description = "RDS instance class"
     type        = string
     default     = "db.t3.small"
   }
   
   variable "db_allocated_storage" {
     description = "Initial storage allocation"
     type        = number
     default     = 50
   }
   
   variable "db_max_allocated_storage" {
     description = "Maximum storage allocation"
     type        = number
     default     = 200
   }
   
   variable "database_name" {
     description = "Name of the database"
     type        = string
     default     = "taskmanager"
   }
   
   variable "database_username" {
     description = "Database username"
     type        = string
     default     = "taskuser"
   }
   
   variable "db_backup_retention_period" {
     description = "Backup retention period in days"
     type        = number
     default     = 14
   }
   
   variable "db_deletion_protection" {
     description = "Enable deletion protection"
     type        = bool
     default     = true
   }
   
   variable "db_skip_final_snapshot" {
     description = "Skip final snapshot on deletion"
     type        = bool
     default     = false
   }
   
   # EC2 Configuration
   variable "ec2_instance_type" {
     description = "EC2 instance type"
     type        = string
     default     = "t3.small"
   }
   
   variable "key_name" {
     description = "EC2 Key Pair name"
     type        = string
     default     = "taskmanager-staging"
   }
   
   variable "asg_min_size" {
     description = "Minimum number of instances"
     type        = number
     default     = 2
   }
   
   variable "asg_max_size" {
     description = "Maximum number of instances"
     type        = number
     default     = 6
   }
   
   variable "asg_desired_capacity" {
     description = "Desired number of instances"
     type        = number
     default     = 2
   }
   
   # ALB Configuration
   variable "alb_deletion_protection" {
     description = "Enable deletion protection for ALB"
     type        = bool
     default     = true
   }
   
   variable "ssl_certificate_arn" {
     description = "ARN of SSL certificate for HTTPS"
     type        = string
     default     = ""
   }
   
   # Monitoring Configuration
   variable "log_retention_days" {
     description = "Log retention period in days"
     type        = number
     default     = 30
   }
   
   variable "alert_email_addresses" {
     description = "List of email addresses for alerts"
     type        = list(string)
     default     = ["devops-team@example.com"]
   }
   
   variable "slack_webhook_url" {
     description = "Slack webhook URL for notifications"
     type        = string
     default     = ""
   }
   
   variable "pagerduty_endpoint" {
     description = "PagerDuty endpoint for critical alerts"
     type        = string
     default     = ""
   }
   
   variable "alert_phone_numbers" {
     description = "List of phone numbers for SMS alerts"
     type        = list(string)
     default     = []
   }
   ```

4. **Create `terraform/environments/staging/outputs.tf`:**
   ```hcl
   # Network Outputs
   output "vpc_id" {
     description = "ID of the VPC"
     value       = module.vpc.vpc_id
   }
   
   output "public_subnet_ids" {
     description = "IDs of the public subnets"
     value       = module.vpc.public_subnet_ids
   }
   
   output "private_subnet_ids" {
     description = "IDs of the private subnets"
     value       = module.vpc.private_subnet_ids
   }
   
   # Database Outputs
   output "db_endpoint" {
     description = "RDS instance endpoint"
     value       = module.database.db_endpoint
     sensitive   = true
   }
   
   output "db_instance_id" {
     description = "RDS instance ID"
     value       = module.database.db_instance_id
   }
   
   # Load Balancer Outputs
   output "alb_dns_name" {
     description = "DNS name of the Application Load Balancer"
     value       = module.alb.alb_dns_name
   }
   
   output "alb_zone_id" {
     description = "Zone ID of the Application Load Balancer"
     value       = module.alb.alb_zone_id
   }
   
   # Auto Scaling Group Outputs
   output "asg_name" {
     description = "Name of the Auto Scaling Group"
     value       = module.ec2.autoscaling_group_name
   }
   
   # ECR Repository Output
   output "ecr_repository_url" {
     description = "ECR repository URL"
     value       = module.ecr.repository_url
   }
   
   # Application URL
   output "application_url" {
     description = "Application URL"
     value       = "http://${module.alb.alb_dns_name}"
   }
   ```

### Task 2: Create Production Environment Configuration

1. **Create production environment directory:**
   ```bash
   mkdir -p terraform/environments/prod
   cd terraform/environments/prod
   ```

2. **Create `terraform/environments/prod/main.tf`:**
   ```hcl
   # Production Environment Configuration
   terraform {
     required_version = ">= 1.0"
     
     backend "s3" {
       bucket = "taskmanager-terraform-state-prod"
       key    = "prod/terraform.tfstate"
       region = "us-east-1"
       
       dynamodb_table = "taskmanager-terraform-locks"
       encrypt        = true
     }
     
     required_providers {
       aws = {
         source  = "hashicorp/aws"
         version = "~> 5.0"
       }
     }
   }
   
   provider "aws" {
     region = var.aws_region
     
     default_tags {
       tags = {
         Environment = "production"
         Project     = var.project_name
         ManagedBy   = "terraform"
         Owner       = "devops-team"
         CostCenter  = "production"
       }
     }
   }
   
   # Use the same module structure as staging but with production-specific variables
   # [Same module configuration as staging but with production variable values]
   ```

3. **Create `terraform/environments/prod/variables.tf`:**
   ```hcl
   # Production-specific variable defaults
   variable "project_name" {
     description = "Name of the project"
     type        = string
     default     = "taskmanager"
   }
   
   variable "environment" {
     description = "Environment name"
     type        = string
     default     = "prod"
   }
   
   variable "aws_region" {
     description = "AWS region"
     type        = string
     default     = "us-east-1"
   }
   
   # VPC Configuration - Different CIDR for production
   variable "vpc_cidr" {
     description = "CIDR block for VPC"
     type        = string
     default     = "10.2.0.0/16"
   }
   
   variable "public_subnet_cidrs" {
     description = "CIDR blocks for public subnets"
     type        = list(string)
     default     = ["10.2.1.0/24", "10.2.2.0/24"]
   }
   
   variable "private_subnet_cidrs" {
     description = "CIDR blocks for private subnets"
     type        = list(string)
     default     = ["10.2.3.0/24", "10.2.4.0/24"]
   }
   
   variable "database_subnet_cidrs" {
     description = "CIDR blocks for database subnets"
     type        = list(string)
     default     = ["10.2.5.0/24", "10.2.6.0/24"]
   }
   
   # Production Database Configuration - Larger instances
   variable "db_instance_class" {
     description = "RDS instance class"
     type        = string
     default     = "db.t3.medium"
   }
   
   variable "db_allocated_storage" {
     description = "Initial storage allocation"
     type        = number
     default     = 100
   }
   
   variable "db_max_allocated_storage" {
     description = "Maximum storage allocation"
     type        = number
     default     = 500
   }
   
   variable "db_backup_retention_period" {
     description = "Backup retention period in days"
     type        = number
     default     = 30
   }
   
   variable "db_deletion_protection" {
     description = "Enable deletion protection"
     type        = bool
     default     = true
   }
   
   variable "db_skip_final_snapshot" {
     description = "Skip final snapshot on deletion"
     type        = bool
     default     = false
   }
   
   # Production EC2 Configuration - Larger instances
   variable "ec2_instance_type" {
     description = "EC2 instance type"
     type        = string
     default     = "t3.medium"
   }
   
   variable "key_name" {
     description = "EC2 Key Pair name"
     type        = string
     default     = "taskmanager-prod"
   }
   
   variable "asg_min_size" {
     description = "Minimum number of instances"
     type        = number
     default     = 3
   }
   
   variable "asg_max_size" {
     description = "Maximum number of instances"
     type        = number
     default     = 10
   }
   
   variable "asg_desired_capacity" {
     description = "Desired number of instances"
     type        = number
     default     = 3
   }
   
   # Production monitoring - Longer retention
   variable "log_retention_days" {
     description = "Log retention period in days"
     type        = number
     default     = 90
   }
   
   variable "alert_email_addresses" {
     description = "List of email addresses for alerts"
     type        = list(string)
     default     = ["ops-team@example.com", "management@example.com"]
   }
   
   variable "alert_phone_numbers" {
     description = "List of phone numbers for SMS alerts"
     type        = list(string)
     default     = ["+1234567890", "+1234567891"]
   }
   ```

### Task 3: Create Terraform State Management

1. **Create `scripts/setup-terraform-backend.sh`:**
   ```bash
   #!/bin/bash
   
   set -e
   
   # Configuration
   PROJECT_NAME="taskmanager"
   REGION="us-east-1"
   
   # Create S3 buckets for Terraform state
   for ENV in dev staging prod; do
     BUCKET_NAME="${PROJECT_NAME}-terraform-state-${ENV}"
     
     echo "Creating S3 bucket: $BUCKET_NAME"
     aws s3api create-bucket \
       --bucket $BUCKET_NAME \
       --region $REGION
     
     # Enable versioning
     aws s3api put-bucket-versioning \
       --bucket $BUCKET_NAME \
       --versioning-configuration Status=Enabled
     
     # Enable encryption
     aws s3api put-bucket-encryption \
       --bucket $BUCKET_NAME \
       --server-side-encryption-configuration '{
         "Rules": [{
           "ApplyServerSideEncryptionByDefault": {
             "SSEAlgorithm": "AES256"
           }
         }]
       }'
     
     # Block public access
     aws s3api put-public-access-block \
       --bucket $BUCKET_NAME \
       --public-access-block-configuration \
       BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
   done
   
   # Create DynamoDB table for state locking
   TABLE_NAME="${PROJECT_NAME}-terraform-locks"
   
   echo "Creating DynamoDB table: $TABLE_NAME"
   aws dynamodb create-table \
     --table-name $TABLE_NAME \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
     --region $REGION
   
   # Wait for table to be created
   aws dynamodb wait table-exists --table-name $TABLE_NAME --region $REGION
   
   echo "Terraform backend setup completed!"
   ```

2. **Make script executable and run:**
   ```bash
   chmod +x scripts/setup-terraform-backend.sh
   ./scripts/setup-terraform-backend.sh
   ```

### ✅ Verification

1. **Check S3 buckets:**
   ```bash
   aws s3 ls | grep taskmanager-terraform-state
   ```

2. **Check DynamoDB table:**
   ```bash
   aws dynamodb describe-table --table-name taskmanager-terraform-locks --query 'Table.TableStatus'
   ```

---

## Exercise 2: Deploy Staging and Production Environments

### Task 1: Deploy Staging Environment

1. **Initialize staging environment:**
   ```bash
   cd terraform/environments/staging
   terraform init
   ```

2. **Create staging variables file:**
   ```bash
   cat > terraform.tfvars << EOF
   # Staging Environment Variables
   project_name = "taskmanager"
   environment  = "staging"
   aws_region   = "us-east-1"
   
   # VPC Configuration
   vpc_cidr = "10.1.0.0/16"
   public_subnet_cidrs   = ["10.1.1.0/24", "10.1.2.0/24"]
   private_subnet_cidrs  = ["10.1.3.0/24", "10.1.4.0/24"]
   database_subnet_cidrs = ["10.1.5.0/24", "10.1.6.0/24"]
   
   # Database Configuration
   db_instance_class = "db.t3.small"
   db_allocated_storage = 50
   db_backup_retention_period = 14
   db_deletion_protection = true
   
   # EC2 Configuration
   ec2_instance_type = "t3.small"
   key_name = "taskmanager-staging"
   asg_min_size = 2
   asg_max_size = 6
   asg_desired_capacity = 2
   
   # Monitoring Configuration
   log_retention_days = 30
   alert_email_addresses = ["devops-team@example.com"]
   EOF
   ```

3. **Create staging key pair:**
   ```bash
   aws ec2 create-key-pair \
     --key-name taskmanager-staging \
     --query 'KeyMaterial' \
     --output text > taskmanager-staging.pem
   
   chmod 400 taskmanager-staging.pem
   ```

4. **Deploy staging environment:**
   ```bash
   terraform plan -var-file=terraform.tfvars
   terraform apply -var-file=terraform.tfvars
   ```

### Task 2: Deploy Production Environment

1. **Initialize production environment:**
   ```bash
   cd terraform/environments/prod
   terraform init
   ```

2. **Create production variables file:**
   ```bash
   cat > terraform.tfvars << EOF
   # Production Environment Variables
   project_name = "taskmanager"
   environment  = "prod"
   aws_region   = "us-east-1"
   
   # VPC Configuration
   vpc_cidr = "10.2.0.0/16"
   public_subnet_cidrs   = ["10.2.1.0/24", "10.2.2.0/24"]
   private_subnet_cidrs  = ["10.2.3.0/24", "10.2.4.0/24"]
   database_subnet_cidrs = ["10.2.5.0/24", "10.2.6.0/24"]
   
   # Database Configuration
   db_instance_class = "db.t3.medium"
   db_allocated_storage = 100
   db_backup_retention_period = 30
   db_deletion_protection = true
   
   # EC2 Configuration
   ec2_instance_type = "t3.medium"
   key_name = "taskmanager-prod"
   asg_min_size = 3
   asg_max_size = 10
   asg_desired_capacity = 3
   
   # Monitoring Configuration
   log_retention_days = 90
   alert_email_addresses = ["ops-team@example.com", "management@example.com"]
   alert_phone_numbers = ["+1234567890", "+1234567891"]
   EOF
   ```

3. **Create production key pair:**
   ```bash
   aws ec2 create-key-pair \
     --key-name taskmanager-prod \
     --query 'KeyMaterial' \
     --output text > taskmanager-prod.pem
   
   chmod 400 taskmanager-prod.pem
   ```

4. **Deploy production environment:**
   ```bash
   terraform plan -var-file=terraform.tfvars
   terraform apply -var-file=terraform.tfvars
   ```

### Task 3: Verify Environment Deployments

1. **Check staging deployment:**
   ```bash
   cd terraform/environments/staging
   STAGING_URL=$(terraform output -raw application_url)
   echo "Staging URL: $STAGING_URL"
   
   # Test staging application
   curl -f "$STAGING_URL/health"
   ```

2. **Check production deployment:**
   ```bash
   cd terraform/environments/prod
   PROD_URL=$(terraform output -raw application_url)
   echo "Production URL: $PROD_URL"
   
   # Test production application
   curl -f "$PROD_URL/health"
   ```

3. **Verify environment isolation:**
   ```bash
   # Check VPC isolation
   aws ec2 describe-vpcs --filters "Name=tag:Project,Values=taskmanager" \
     --query 'Vpcs[*].[VpcId,CidrBlock,Tags[?Key==`Environment`].Value|[0]]' \
     --output table
   ```

### ✅ Verification

1. **All environments deployed:**
   ```bash
   for env in dev staging prod; do
     echo "Checking $env environment:"
     cd terraform/environments/$env
     terraform show -json | jq '.values.root_module.resources | length'
   done
   ```

2. **Applications accessible:**
   ```bash
   for env in dev staging prod; do
     URL=$(cd terraform/environments/$env && terraform output -raw application_url)
     echo "Testing $env: $URL"
     curl -f "$URL/health" && echo "✅ $env OK" || echo "❌ $env FAILED"
   done
   ```

---

## Exercise 3: Implement Environment Promotion Workflows

### Task 1: Create Environment Promotion Pipeline

1. **Create `.github/workflows/environment-promotion.yml`:**
   ```yaml
   name: Environment Promotion
   
   on:
     workflow_dispatch:
       inputs:
         from_environment:
           description: 'Source environment'
           required: true
           type: choice
           options:
             - dev
             - staging
         to_environment:
           description: 'Target environment'
           required: true
           type: choice
           options:
             - staging
             - prod
         image_tag:
           description: 'Image tag to promote'
           required: true
           type: string
   
   env:
     AWS_REGION: us-east-1
     PROJECT_NAME: taskmanager
   
   jobs:
     validate-promotion:
       runs-on: ubuntu-latest
       outputs:
         can-promote: ${{ steps.validation.outputs.can-promote }}
       
       steps:
         - name: Checkout code
           uses: actions/checkout@v4
         
         - name: Configure AWS credentials
           uses: aws-actions/configure-aws-credentials@v4
           with:
             aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
             aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
             aws-region: ${{ env.AWS_REGION }}
         
         - name: Validate promotion
           id: validation
           run: |
             FROM_ENV="${{ github.event.inputs.from_environment }}"
             TO_ENV="${{ github.event.inputs.to_environment }}"
             IMAGE_TAG="${{ github.event.inputs.image_tag }}"
             
             echo "Validating promotion from $FROM_ENV to $TO_ENV"
             
             # Check if source environment is healthy
             FROM_ALB=$(aws elbv2 describe-load-balancers \
               --query "LoadBalancers[?contains(LoadBalancerName, '$PROJECT_NAME-$FROM_ENV')].DNSName" \
               --output text)
             
             if [ -n "$FROM_ALB" ]; then
               if curl -f "http://$FROM_ALB/health"; then
                 echo "✅ Source environment ($FROM_ENV) is healthy"
                 echo "can-promote=true" >> $GITHUB_OUTPUT
               else
                 echo "❌ Source environment ($FROM_ENV) is unhealthy"
                 echo "can-promote=false" >> $GITHUB_OUTPUT
               fi
             else
               echo "❌ Source environment ($FROM_ENV) not found"
               echo "can-promote=false" >> $GITHUB_OUTPUT
             fi
             
             # Validate promotion path
             if [ "$FROM_ENV" = "dev" ] && [ "$TO_ENV" = "prod" ]; then
               echo "❌ Cannot promote directly from dev to prod"
               echo "can-promote=false" >> $GITHUB_OUTPUT
             fi
   
     run-tests:
       runs-on: ubuntu-latest
       needs: validate-promotion
       if: needs.validate-promotion.outputs.can-promote == 'true'
       
       steps:
         - name: Checkout code
           uses: actions/checkout@v4
         
         - name: Configure AWS credentials
           uses: aws-actions/configure-aws-credentials@v4
           with:
             aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
             aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
             aws-region: ${{ env.AWS_REGION }}
         
         - name: Run promotion tests
           run: |
             FROM_ENV="${{ github.event.inputs.from_environment }}"
             IMAGE_TAG="${{ github.event.inputs.image_tag }}"
             
             echo "Running promotion tests for $FROM_ENV environment"
             
             # Get ALB DNS
             ALB_DNS=$(aws elbv2 describe-load-balancers \
               --query "LoadBalancers[?contains(LoadBalancerName, '$PROJECT_NAME-$FROM_ENV')].DNSName" \
               --output text)
             
             # Run comprehensive tests
             .github/scripts/promotion-tests.sh $FROM_ENV $ALB_DNS
   
     promote:
       runs-on: ubuntu-latest
       needs: [validate-promotion, run-tests]
       if: needs.validate-promotion.outputs.can-promote == 'true'
       environment: ${{ github.event.inputs.to_environment }}
       
       steps:
         - name: Checkout code
           uses: actions/checkout@v4
         
         - name: Configure AWS credentials
           uses: aws-actions/configure-aws-credentials@v4
           with:
             aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
             aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
             aws-region: ${{ env.AWS_REGION }}
         
         - name: Promote to target environment
           run: |
             TO_ENV="${{ github.event.inputs.to_environment }}"
             IMAGE_TAG="${{ github.event.inputs.image_tag }}"
             
             echo "Promoting image $IMAGE_TAG to $TO_ENV environment"
             
             # Deploy to target environment
             .github/scripts/deploy.sh $TO_ENV $IMAGE_TAG
         
         - name: Verify promotion
           run: |
             TO_ENV="${{ github.event.inputs.to_environment }}"
             
             echo "Verifying promotion to $TO_ENV"
             
             # Wait for deployment to complete
             sleep 60
             
             # Run smoke tests
             .github/scripts/smoke-tests.sh $TO_ENV
         
         - name: Create promotion record
           run: |
             FROM_ENV="${{ github.event.inputs.from_environment }}"
             TO_ENV="${{ github.event.inputs.to_environment }}"
             IMAGE_TAG="${{ github.event.inputs.image_tag }}"
             
             # Create promotion record in DynamoDB
             aws dynamodb put-item \
               --table-name "$PROJECT_NAME-promotions" \
               --item '{
                 "promotion_id": {"S": "'$(date +%s)'"},
                 "from_environment": {"S": "'$FROM_ENV'"},
                 "to_environment": {"S": "'$TO_ENV'"},
                 "image_tag": {"S": "'$IMAGE_TAG'"},
                 "promoted_at": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"},
                 "promoted_by": {"S": "'${{ github.actor }}'"}
               }'
         
         - name: Notify promotion success
           if: success()
           uses: 8398a7/action-slack@v3
           with:
             status: success
             channel: '#deployments'
             webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
             text: |
               ✅ Successfully promoted ${{ github.event.inputs.image_tag }} from ${{ github.event.inputs.from_environment }} to ${{ github.event.inputs.to_environment }}
               
               Promoted by: ${{ github.actor }}
               Workflow: ${{ github.workflow }}
         
         - name: Notify promotion failure
           if: failure()
           uses: 8398a7/action-slack@v3
           with:
             status: failure
             channel: '#deployments'
             webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
             text: |
               ❌ Failed to promote ${{ github.event.inputs.image_tag }} from ${{ github.event.inputs.from_environment }} to ${{ github.event.inputs.to_environment }}
               
               Promoted by: ${{ github.actor }}
               Workflow: ${{ github.workflow }}
   ```

2. **Create `.github/scripts/promotion-tests.sh`:**
   ```bash
   #!/bin/bash
   
   set -e
   
   ENVIRONMENT=$1
   ALB_DNS=$2
   
   if [ -z "$ENVIRONMENT" ] || [ -z "$ALB_DNS" ]; then
       echo "Usage: $0 <environment> <alb_dns>"
       exit 1
   fi
   
   BASE_URL="http://$ALB_DNS"
   
   echo "Running promotion tests for $ENVIRONMENT environment"
   echo "Base URL: $BASE_URL"
   
   # Test 1: Health check
   echo "Test 1: Health check"
   if curl -f -s "$BASE_URL/health" | jq -e '.status == "healthy"'; then
       echo "✅ Health check passed"
   else
       echo "❌ Health check failed"
       exit 1
   fi
   
   # Test 2: Database connectivity
   echo "Test 2: Database connectivity"
   if curl -f -s "$BASE_URL/api/users" | jq -e '.users'; then
       echo "✅ Database connectivity test passed"
   else
       echo "❌ Database connectivity test failed"
       exit 1
   fi
   
   # Test 3: Load test
   echo "Test 3: Load test"
   for i in {1..50}; do
       curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/dashboard-stats" &
   done
   wait
   
   # Check if all requests succeeded
   if curl -f -s "$BASE_URL/health" | jq -e '.status == "healthy"'; then
       echo "✅ Load test passed"
   else
       echo "❌ Load test failed"
       exit 1
   fi
   
   # Test 4: Performance test
   echo "Test 4: Performance test"
   RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" "$BASE_URL/api/dashboard-stats")
   
   if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
       echo "✅ Performance test passed (${RESPONSE_TIME}s)"
   else
       echo "❌ Performance test failed (${RESPONSE_TIME}s)"
       exit 1
   fi
   
   # Test 5: Security test
   echo "Test 5: Security test"
   STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/admin")
   
   if [ "$STATUS_CODE" -eq 401 ] || [ "$STATUS_CODE" -eq 403 ] || [ "$STATUS_CODE" -eq 404 ]; then
       echo "✅ Security test passed (status: $STATUS_CODE)"
   else
       echo "❌ Security test failed (status: $STATUS_CODE)"
       exit 1
   fi
   
   echo "All promotion tests passed for $ENVIRONMENT environment"
   ```

3. **Make script executable:**
   ```bash
   chmod +x .github/scripts/promotion-tests.sh
   ```

### Task 2: Create Promotion Tracking

1. **Create DynamoDB table for promotions:**
   ```bash
   aws dynamodb create-table \
     --table-name "taskmanager-promotions" \
     --attribute-definitions AttributeName=promotion_id,AttributeType=S \
     --key-schema AttributeName=promotion_id,KeyType=HASH \
     --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
     --region us-east-1
   ```

2. **Create promotion tracking script:**
   ```bash
   cat > scripts/check-promotions.sh << 'EOF'
   #!/bin/bash
   
   set -e
   
   echo "Recent promotions:"
   aws dynamodb scan \
     --table-name "taskmanager-promotions" \
     --query 'Items[*].[promotion_id.S, from_environment.S, to_environment.S, image_tag.S, promoted_at.S, promoted_by.S]' \
     --output table
   EOF
   
   chmod +x scripts/check-promotions.sh
   ```

### ✅ Verification

1. **Test promotion workflow:**
   ```bash
   # Trigger promotion from dev to staging
   gh workflow run environment-promotion.yml \
     -f from_environment=dev \
     -f to_environment=staging \
     -f image_tag=latest
   ```

2. **Check promotion tracking:**
   ```bash
   ./scripts/check-promotions.sh
   ```

---

## Exercise 4: Set up Cross-Environment Monitoring

### Task 1: Create Cross-Environment Dashboard

1. **Create `terraform/modules/monitoring/cross-environment-dashboard.tf`:**
   ```hcl
   # Cross-Environment Monitoring Dashboard
   resource "aws_cloudwatch_dashboard" "cross_environment" {
     dashboard_name = "${var.project_name}-cross-environment-monitoring"
   
     dashboard_body = jsonencode({
       widgets = [
         {
           type   = "metric"
           x      = 0
           y      = 0
           width  = 8
           height = 6
   
           properties = {
             metrics = [
               ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", "${var.project_name}-dev-alb"],
               [".", ".", ".", "${var.project_name}-staging-alb"],
               [".", ".", ".", "${var.project_name}-prod-alb"]
             ]
             period = 300
             stat   = "Sum"
             region = var.aws_region
             title  = "Request Count - All Environments"
             yAxis = {
               left = {
                 min = 0
               }
             }
           }
         },
         {
           type   = "metric"
           x      = 8
           y      = 0
           width  = 8
           height = 6
   
           properties = {
             metrics = [
               ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", "${var.project_name}-dev-alb"],
               [".", ".", ".", "${var.project_name}-staging-alb"],
               [".", ".", ".", "${var.project_name}-prod-alb"]
             ]
             period = 300
             stat   = "Average"
             region = var.aws_region
             title  = "Response Time - All Environments"
             yAxis = {
               left = {
                 min = 0
               }
             }
           }
         },
         {
           type   = "metric"
           x      = 16
           y      = 0
           width  = 8
           height = 6
   
           properties = {
             metrics = [
               ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", "${var.project_name}-dev-alb"],
               [".", ".", ".", "${var.project_name}-staging-alb"],
               [".", ".", ".", "${var.project_name}-prod-alb"]
             ]
             period = 300
             stat   = "Sum"
             region = var.aws_region
             title  = "Error Count - All Environments"
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
           y      = 6
           width  = 12
           height = 6
   
           properties = {
             metrics = [
               ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", "${var.project_name}-dev-db"],
               [".", ".", ".", "${var.project_name}-staging-db"],
               [".", ".", ".", "${var.project_name}-prod-db"]
             ]
             period = 300
             stat   = "Average"
             region = var.aws_region
             title  = "Database CPU - All Environments"
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
           x      = 12
           y      = 6
           width  = 12
           height = 6
   
           properties = {
             metrics = [
               ["AWS/EC2", "CPUUtilization", "AutoScalingGroupName", "${var.project_name}-dev-web-asg"],
               [".", ".", ".", "${var.project_name}-staging-web-asg"],
               [".", ".", ".", "${var.project_name}-prod-web-asg"]
             ]
             period = 300
             stat   = "Average"
             region = var.aws_region
             title  = "EC2 CPU - All Environments"
             yAxis = {
               left = {
                 min = 0
                 max = 100
               }
             }
           }
         }
       ]
     })
   }
   ```

### Task 2: Create Environment Comparison Report

1. **Create `scripts/environment-comparison.sh`:**
   ```bash
   #!/bin/bash
   
   set -e
   
   echo "=== Environment Comparison Report ==="
   echo "Generated at: $(date)"
   echo
   
   # Infrastructure Comparison
   echo "### Infrastructure Comparison"
   echo
   
   for env in dev staging prod; do
     echo "#### $env Environment:"
     
     # Get VPC info
     VPC_ID=$(aws ec2 describe-vpcs \
       --filters "Name=tag:Project,Values=taskmanager" "Name=tag:Environment,Values=$env" \
       --query 'Vpcs[0].VpcId' --output text)
     
     if [ "$VPC_ID" != "None" ]; then
       echo "- VPC ID: $VPC_ID"
       
       # Get instance count
       INSTANCE_COUNT=$(aws ec2 describe-instances \
         --filters "Name=vpc-id,Values=$VPC_ID" "Name=instance-state-name,Values=running" \
         --query 'length(Reservations[].Instances[])')
       echo "- Running Instances: $INSTANCE_COUNT"
       
       # Get ALB info
       ALB_DNS=$(aws elbv2 describe-load-balancers \
         --query "LoadBalancers[?contains(LoadBalancerName, 'taskmanager-$env')].DNSName" \
         --output text)
       echo "- ALB DNS: ${ALB_DNS:-Not found}"
       
       # Get database info
       DB_INSTANCE=$(aws rds describe-db-instances \
         --query "DBInstances[?contains(DBInstanceIdentifier, 'taskmanager-$env')].DBInstanceClass" \
         --output text)
       echo "- Database Instance: ${DB_INSTANCE:-Not found}"
       
       # Get Auto Scaling Group info
       ASG_CAPACITY=$(aws autoscaling describe-auto-scaling-groups \
         --query "AutoScalingGroups[?contains(AutoScalingGroupName, 'taskmanager-$env')].DesiredCapacity" \
         --output text)
       echo "- ASG Desired Capacity: ${ASG_CAPACITY:-Not found}"
       
       echo
     else
       echo "- Environment not found"
       echo
     fi
   done
   
   # Performance Comparison
   echo "### Performance Comparison (Last 1 Hour)"
   echo
   
   END_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)
   START_TIME=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)
   
   for env in dev staging prod; do
     echo "#### $env Environment:"
     
     # Get ALB metrics
     ALB_NAME=$(aws elbv2 describe-load-balancers \
       --query "LoadBalancers[?contains(LoadBalancerName, 'taskmanager-$env')].LoadBalancerArn" \
       --output text | cut -d'/' -f2-)
     
     if [ -n "$ALB_NAME" ]; then
       # Request count
       REQUEST_COUNT=$(aws cloudwatch get-metric-statistics \
         --namespace AWS/ApplicationELB \
         --metric-name RequestCount \
         --dimensions Name=LoadBalancer,Value=$ALB_NAME \
         --start-time $START_TIME \
         --end-time $END_TIME \
         --period 3600 \
         --statistics Sum \
         --query 'Datapoints[0].Sum' \
         --output text)
       echo "- Total Requests: ${REQUEST_COUNT:-0}"
       
       # Average response time
       RESPONSE_TIME=$(aws cloudwatch get-metric-statistics \
         --namespace AWS/ApplicationELB \
         --metric-name TargetResponseTime \
         --dimensions Name=LoadBalancer,Value=$ALB_NAME \
         --start-time $START_TIME \
         --end-time $END_TIME \
         --period 3600 \
         --statistics Average \
         --query 'Datapoints[0].Average' \
         --output text)
       echo "- Avg Response Time: ${RESPONSE_TIME:-0}s"
       
       # Error count
       ERROR_COUNT=$(aws cloudwatch get-metric-statistics \
         --namespace AWS/ApplicationELB \
         --metric-name HTTPCode_Target_5XX_Count \
         --dimensions Name=LoadBalancer,Value=$ALB_NAME \
         --start-time $START_TIME \
         --end-time $END_TIME \
         --period 3600 \
         --statistics Sum \
         --query 'Datapoints[0].Sum' \
         --output text)
       echo "- Total Errors: ${ERROR_COUNT:-0}"
       
       echo
     else
       echo "- No ALB found"
       echo
     fi
   done
   
   # Cost Comparison (requires AWS Cost Explorer API)
   echo "### Cost Comparison"
   echo "Note: Enable AWS Cost Explorer API for detailed cost analysis"
   echo
   
   for env in dev staging prod; do
     echo "#### $env Environment:"
     echo "- Cost analysis requires AWS Cost Explorer API"
     echo "- Use AWS Cost Explorer console for detailed cost breakdown"
     echo
   done
   
   echo "=== End of Report ==="
   ```

2. **Make script executable:**
   ```bash
   chmod +x scripts/environment-comparison.sh
   ```

### Task 3: Create Environment Health Check

1. **Create `scripts/environment-health-check.sh`:**
   ```bash
   #!/bin/bash
   
   set -e
   
   echo "=== Multi-Environment Health Check ==="
   echo "Timestamp: $(date)"
   echo
   
   # Colors for output
   RED='\033[0;31m'
   GREEN='\033[0;32m'
   YELLOW='\033[1;33m'
   NC='\033[0m' # No Color
   
   OVERALL_STATUS=0
   
   for env in dev staging prod; do
     echo "### $env Environment Health Check"
     ENV_STATUS=0
     
     # Check ALB health
     ALB_DNS=$(aws elbv2 describe-load-balancers \
       --query "LoadBalancers[?contains(LoadBalancerName, 'taskmanager-$env')].DNSName" \
       --output text)
     
     if [ -n "$ALB_DNS" ] && [ "$ALB_DNS" != "None" ]; then
       if curl -f -s "http://$ALB_DNS/health" > /dev/null 2>&1; then
         echo -e "✅ ALB Health: ${GREEN}HEALTHY${NC}"
       else
         echo -e "❌ ALB Health: ${RED}UNHEALTHY${NC}"
         ENV_STATUS=1
       fi
     else
       echo -e "❌ ALB: ${RED}NOT FOUND${NC}"
       ENV_STATUS=1
     fi
     
     # Check target group health
     TG_ARN=$(aws elbv2 describe-target-groups \
       --query "TargetGroups[?contains(TargetGroupName, 'taskmanager-$env')].TargetGroupArn" \
       --output text)
     
     if [ -n "$TG_ARN" ] && [ "$TG_ARN" != "None" ]; then
       HEALTHY_TARGETS=$(aws elbv2 describe-target-health \
         --target-group-arn $TG_ARN \
         --query 'TargetHealthDescriptions[?TargetHealth.State==`healthy`]' \
         --output text | wc -l)
       
       TOTAL_TARGETS=$(aws elbv2 describe-target-health \
         --target-group-arn $TG_ARN \
         --query 'length(TargetHealthDescriptions)')
       
       if [ "$HEALTHY_TARGETS" -gt 0 ]; then
         echo -e "✅ Target Health: ${GREEN}$HEALTHY_TARGETS/$TOTAL_TARGETS HEALTHY${NC}"
       else
         echo -e "❌ Target Health: ${RED}$HEALTHY_TARGETS/$TOTAL_TARGETS HEALTHY${NC}"
         ENV_STATUS=1
       fi
     else
       echo -e "❌ Target Group: ${RED}NOT FOUND${NC}"
       ENV_STATUS=1
     fi
     
     # Check database health
     DB_INSTANCE=$(aws rds describe-db-instances \
       --query "DBInstances[?contains(DBInstanceIdentifier, 'taskmanager-$env')].DBInstanceStatus" \
       --output text)
     
     if [ "$DB_INSTANCE" = "available" ]; then
       echo -e "✅ Database: ${GREEN}AVAILABLE${NC}"
     elif [ -n "$DB_INSTANCE" ]; then
       echo -e "⚠️  Database: ${YELLOW}$DB_INSTANCE${NC}"
       ENV_STATUS=1
     else
       echo -e "❌ Database: ${RED}NOT FOUND${NC}"
       ENV_STATUS=1
     fi
     
     # Check Auto Scaling Group health
     ASG_NAME=$(aws autoscaling describe-auto-scaling-groups \
       --query "AutoScalingGroups[?contains(AutoScalingGroupName, 'taskmanager-$env')].AutoScalingGroupName" \
       --output text)
     
     if [ -n "$ASG_NAME" ] && [ "$ASG_NAME" != "None" ]; then
       HEALTHY_INSTANCES=$(aws autoscaling describe-auto-scaling-groups \
         --auto-scaling-group-names $ASG_NAME \
         --query 'AutoScalingGroups[0].Instances[?HealthStatus==`Healthy`]' \
         --output text | wc -l)
       
       TOTAL_INSTANCES=$(aws autoscaling describe-auto-scaling-groups \
         --auto-scaling-group-names $ASG_NAME \
         --query 'length(AutoScalingGroups[0].Instances)')
       
       if [ "$HEALTHY_INSTANCES" -gt 0 ]; then
         echo -e "✅ ASG Health: ${GREEN}$HEALTHY_INSTANCES/$TOTAL_INSTANCES HEALTHY${NC}"
       else
         echo -e "❌ ASG Health: ${RED}$HEALTHY_INSTANCES/$TOTAL_INSTANCES HEALTHY${NC}"
         ENV_STATUS=1
       fi
     else
       echo -e "❌ Auto Scaling Group: ${RED}NOT FOUND${NC}"
       ENV_STATUS=1
     fi
     
     # Environment overall status
     if [ $ENV_STATUS -eq 0 ]; then
       echo -e "Overall Status: ${GREEN}HEALTHY${NC}"
     else
       echo -e "Overall Status: ${RED}UNHEALTHY${NC}"
       OVERALL_STATUS=1
     fi
     
     echo
   done
   
   # Summary
   echo "=== Summary ==="
   if [ $OVERALL_STATUS -eq 0 ]; then
     echo -e "All environments are ${GREEN}HEALTHY${NC}"
   else
     echo -e "One or more environments are ${RED}UNHEALTHY${NC}"
   fi
   
   exit $OVERALL_STATUS
   ```

2. **Make script executable:**
   ```bash
   chmod +x scripts/environment-health-check.sh
   ```

### ✅ Verification

1. **Run environment comparison:**
   ```bash
   ./scripts/environment-comparison.sh
   ```

2. **Run health check:**
   ```bash
   ./scripts/environment-health-check.sh
   ```

3. **Check cross-environment dashboard:**
   ```bash
   aws cloudwatch get-dashboard --dashboard-name "taskmanager-cross-environment-monitoring"
   ```

---

## Exercise 5: Create Disaster Recovery and Rollback Procedures

### Task 1: Create Disaster Recovery Plan

1. **Create `docs/disaster-recovery-plan.md`:**
   ```markdown
   # Disaster Recovery Plan - TaskManager Application
   
   ## Overview
   This document outlines the disaster recovery procedures for the TaskManager application across all environments.
   
   ## Recovery Time Objective (RTO)
   - **Development**: 4 hours
   - **Staging**: 2 hours
   - **Production**: 30 minutes
   
   ## Recovery Point Objective (RPO)
   - **Development**: 24 hours
   - **Staging**: 4 hours
   - **Production**: 1 hour
   
   ## Disaster Scenarios
   
   ### Scenario 1: Application Failure
   **Symptoms**: Application returns 5XX errors, health checks fail
   **Response**:
   1. Check Auto Scaling Group health
   2. Review CloudWatch logs for errors
   3. Restart unhealthy instances
   4. If persistent, rollback to previous version
   
   ### Scenario 2: Database Failure
   **Symptoms**: Database connection errors, timeout errors
   **Response**:
   1. Check RDS instance status
   2. Review database logs
   3. Restart database if needed
   4. Restore from backup if corrupted
   
   ### Scenario 3: Infrastructure Failure
   **Symptoms**: Entire environment unavailable
   **Response**:
   1. Check AWS service health
   2. Verify Terraform state
   3. Re-deploy infrastructure if needed
   4. Restore data from backups
   
   ## Recovery Procedures
   
   ### Database Recovery
   ```bash
   # List available backups
   aws rds describe-db-snapshots --db-instance-identifier taskmanager-prod-db
   
   # Restore from backup
   aws rds restore-db-instance-from-db-snapshot \
     --db-instance-identifier taskmanager-prod-db-restored \
     --db-snapshot-identifier taskmanager-prod-db-snapshot-20240101
   ```
   
   ### Application Recovery
   ```bash
   # Rollback to previous version
   gh workflow run rollback.yml \
     -f environment=prod \
     -f version=previous-known-good-version
   ```
   
   ### Infrastructure Recovery
   ```bash
   # Re-deploy infrastructure
   cd terraform/environments/prod
   terraform plan
   terraform apply
   ```
   
   ## Contact Information
   - **On-Call Engineer**: +1-555-ON-CALL
   - **Engineering Manager**: manager@example.com
   - **DevOps Team**: devops@example.com
   ```

2. **Create `scripts/disaster-recovery.sh`:**
   ```bash
   #!/bin/bash
   
   set -e
   
   ENVIRONMENT=$1
   SCENARIO=$2
   
   if [ -z "$ENVIRONMENT" ] || [ -z "$SCENARIO" ]; then
       echo "Usage: $0 <environment> <scenario>"
       echo "Scenarios: app-failure, db-failure, infra-failure"
       exit 1
   fi
   
   echo "=== Disaster Recovery for $ENVIRONMENT - $SCENARIO ==="
   echo "Started at: $(date)"
   
   case $SCENARIO in
       "app-failure")
           echo "Handling application failure..."
           
           # Check Auto Scaling Group
           ASG_NAME=$(aws autoscaling describe-auto-scaling-groups \
               --query "AutoScalingGroups[?contains(AutoScalingGroupName, 'taskmanager-$ENVIRONMENT')].AutoScalingGroupName" \
               --output text)
           
           if [ -n "$ASG_NAME" ]; then
               echo "Found ASG: $ASG_NAME"
               
               # Get unhealthy instances
               UNHEALTHY_INSTANCES=$(aws autoscaling describe-auto-scaling-groups \
                   --auto-scaling-group-names $ASG_NAME \
                   --query 'AutoScalingGroups[0].Instances[?HealthStatus!=`Healthy`].InstanceId' \
                   --output text)
               
               if [ -n "$UNHEALTHY_INSTANCES" ]; then
                   echo "Terminating unhealthy instances: $UNHEALTHY_INSTANCES"
                   for instance in $UNHEALTHY_INSTANCES; do
                       aws autoscaling terminate-instance-in-auto-scaling-group \
                           --instance-id $instance \
                           --should-decrement-desired-capacity
                   done
               fi
               
               # Force instance refresh
               aws autoscaling start-instance-refresh \
                   --auto-scaling-group-name $ASG_NAME \
                   --preferences MinHealthyPercentage=50,InstanceWarmup=300
               
               echo "Instance refresh started"
           fi
           ;;
           
       "db-failure")
           echo "Handling database failure..."
           
           # Check database status
           DB_INSTANCE=$(aws rds describe-db-instances \
               --query "DBInstances[?contains(DBInstanceIdentifier, 'taskmanager-$ENVIRONMENT')].DBInstanceIdentifier" \
               --output text)
           
           if [ -n "$DB_INSTANCE" ]; then
               echo "Found database: $DB_INSTANCE"
               
               DB_STATUS=$(aws rds describe-db-instances \
                   --db-instance-identifier $DB_INSTANCE \
                   --query 'DBInstances[0].DBInstanceStatus' \
                   --output text)
               
               echo "Database status: $DB_STATUS"
               
               if [ "$DB_STATUS" != "available" ]; then
                   echo "Database is not available. Checking for recent snapshots..."
                   
                   LATEST_SNAPSHOT=$(aws rds describe-db-snapshots \
                       --db-instance-identifier $DB_INSTANCE \
                       --snapshot-type automated \
                       --query 'DBSnapshots[0].DBSnapshotIdentifier' \
                       --output text)
                   
                   if [ -n "$LATEST_SNAPSHOT" ]; then
                       echo "Latest snapshot: $LATEST_SNAPSHOT"
                       echo "Manual intervention required for database restore"
                   fi
               fi
           fi
           ;;
           
       "infra-failure")
           echo "Handling infrastructure failure..."
           
           # Check Terraform state
           cd terraform/environments/$ENVIRONMENT
           
           echo "Checking Terraform state..."
           terraform plan -detailed-exitcode
           
           if [ $? -eq 2 ]; then
               echo "Infrastructure drift detected"
               echo "Manual intervention required"
               terraform plan
           else
               echo "Infrastructure state is consistent"
           fi
           ;;
           
       *)
           echo "Unknown scenario: $SCENARIO"
           exit 1
           ;;
   esac
   
   echo "Disaster recovery procedure completed at: $(date)"
   ```

3. **Make script executable:**
   ```bash
   chmod +x scripts/disaster-recovery.sh
   ```

### Task 2: Create Automated Backup Procedures

1. **Create `scripts/backup-all-environments.sh`:**
   ```bash
   #!/bin/bash
   
   set -e
   
   TIMESTAMP=$(date +%Y%m%d_%H%M%S)
   
   echo "=== Automated Backup - All Environments ==="
   echo "Started at: $(date)"
   
   for env in dev staging prod; do
       echo "Backing up $env environment..."
       
       # Database backup
       DB_INSTANCE=$(aws rds describe-db-instances \
           --query "DBInstances[?contains(DBInstanceIdentifier, 'taskmanager-$env')].DBInstanceIdentifier" \
           --output text)
       
       if [ -n "$DB_INSTANCE" ] && [ "$DB_INSTANCE" != "None" ]; then
           echo "Creating database snapshot for $env..."
           
           SNAPSHOT_ID="taskmanager-$env-backup-$TIMESTAMP"
           
           aws rds create-db-snapshot \
               --db-instance-identifier $DB_INSTANCE \
               --db-snapshot-identifier $SNAPSHOT_ID
           
           echo "Database snapshot created: $SNAPSHOT_ID"
       fi
       
       # Terraform state backup
       echo "Backing up Terraform state for $env..."
       
       STATE_BUCKET="taskmanager-terraform-state-$env"
       BACKUP_BUCKET="taskmanager-terraform-backups"
       
       # Create backup bucket if it doesn't exist
       if ! aws s3 ls "s3://$BACKUP_BUCKET" 2>/dev/null; then
           aws s3 mb "s3://$BACKUP_BUCKET"
       fi
       
       # Copy state file
       aws s3 cp "s3://$STATE_BUCKET/$env/terraform.tfstate" \
           "s3://$BACKUP_BUCKET/$env/terraform.tfstate.$TIMESTAMP"
       
       echo "Terraform state backed up for $env"
       
       # Application configuration backup
       echo "Backing up application configuration for $env..."
       
       # Export environment variables and configurations
       mkdir -p backups/$env
       
       # Export ALB configuration
       ALB_ARN=$(aws elbv2 describe-load-balancers \
           --query "LoadBalancers[?contains(LoadBalancerName, 'taskmanager-$env')].LoadBalancerArn" \
           --output text)
       
       if [ -n "$ALB_ARN" ]; then
           aws elbv2 describe-load-balancers \
               --load-balancer-arns $ALB_ARN > backups/$env/alb-config-$TIMESTAMP.json
       fi
       
       # Export ASG configuration
       ASG_NAME=$(aws autoscaling describe-auto-scaling-groups \
           --query "AutoScalingGroups[?contains(AutoScalingGroupName, 'taskmanager-$env')].AutoScalingGroupName" \
           --output text)
       
       if [ -n "$ASG_NAME" ]; then
           aws autoscaling describe-auto-scaling-groups \
               --auto-scaling-group-names $ASG_NAME > backups/$env/asg-config-$TIMESTAMP.json
       fi
       
       echo "Configuration backup completed for $env"
   done
   
   # Clean up old backups (keep last 7 days)
   echo "Cleaning up old backups..."
   
   # Clean up old database snapshots
   for env in dev staging prod; do
       OLD_SNAPSHOTS=$(aws rds describe-db-snapshots \
           --snapshot-type manual \
           --query "DBSnapshots[?contains(DBSnapshotIdentifier, 'taskmanager-$env-backup-') && SnapshotCreateTime < '$(date -d '7 days ago' -u +%Y-%m-%dT%H:%M:%SZ)'].DBSnapshotIdentifier" \
           --output text)
       
       for snapshot in $OLD_SNAPSHOTS; do
           if [ -n "$snapshot" ]; then
               echo "Deleting old snapshot: $snapshot"
               aws rds delete-db-snapshot --db-snapshot-identifier $snapshot
           fi
       done
   done
   
   echo "Backup procedure completed at: $(date)"
   ```

2. **Create automated backup schedule:**
   ```bash
   # Create EventBridge rule for daily backups
   aws events put-rule \
       --name "taskmanager-daily-backup" \
       --schedule-expression "cron(0 2 * * ? *)" \
       --description "Daily backup of TaskManager environments"
   
   # Create Lambda function for backup execution
   cat > backup-lambda.py << 'EOF'
   import boto3
   import subprocess
   import json
   
   def lambda_handler(event, context):
       # Execute backup script
       result = subprocess.run(['/opt/backup-all-environments.sh'], 
                              capture_output=True, text=True)
       
       if result.returncode == 0:
           return {
               'statusCode': 200,
               'body': json.dumps('Backup completed successfully')
           }
       else:
           return {
               'statusCode': 500,
               'body': json.dumps(f'Backup failed: {result.stderr}')
           }
   EOF
   ```

3. **Make backup script executable:**
   ```bash
   chmod +x scripts/backup-all-environments.sh
   ```

### Task 3: Create Rollback Procedures

1. **Create `scripts/rollback-environment.sh`:**
   ```bash
   #!/bin/bash
   
   set -e
   
   ENVIRONMENT=$1
   TARGET_VERSION=$2
   
   if [ -z "$ENVIRONMENT" ] || [ -z "$TARGET_VERSION" ]; then
       echo "Usage: $0 <environment> <target_version>"
       echo "Example: $0 prod v1.2.3"
       exit 1
   fi
   
   echo "=== Rollback $ENVIRONMENT to $TARGET_VERSION ==="
   echo "Started at: $(date)"
   
   # Validate target version exists
   ECR_REPO=$(aws ecr describe-repositories \
       --repository-names "taskmanager-$ENVIRONMENT" \
       --query 'repositories[0].repositoryUri' \
       --output text)
   
   if ! aws ecr describe-images \
       --repository-name "taskmanager-$ENVIRONMENT" \
       --image-ids imageTag=$TARGET_VERSION > /dev/null 2>&1; then
       echo "Error: Image tag $TARGET_VERSION not found in ECR"
       exit 1
   fi
   
   # Create rollback checkpoint
   CHECKPOINT_FILE="rollback-checkpoint-$ENVIRONMENT-$(date +%Y%m%d_%H%M%S).json"
   
   echo "Creating rollback checkpoint..."
   
   # Save current state
   ASG_NAME=$(aws autoscaling describe-auto-scaling-groups \
       --query "AutoScalingGroups[?contains(AutoScalingGroupName, 'taskmanager-$ENVIRONMENT')].AutoScalingGroupName" \
       --output text)
   
   if [ -n "$ASG_NAME" ]; then
       CURRENT_LAUNCH_TEMPLATE=$(aws autoscaling describe-auto-scaling-groups \
           --auto-scaling-group-names $ASG_NAME \
           --query 'AutoScalingGroups[0].LaunchTemplate' \
           --output json)
       
       echo "$CURRENT_LAUNCH_TEMPLATE" > $CHECKPOINT_FILE
       echo "Checkpoint saved to: $CHECKPOINT_FILE"
   fi
   
   # Perform rollback
   echo "Performing rollback to $TARGET_VERSION..."
   
   # Use the deployment script with target version
   .github/scripts/deploy.sh $ENVIRONMENT $TARGET_VERSION
   
   # Wait for rollback to complete
   echo "Waiting for rollback to complete..."
   sleep 60
   
   # Verify rollback
   echo "Verifying rollback..."
   
   ALB_DNS=$(aws elbv2 describe-load-balancers \
       --query "LoadBalancers[?contains(LoadBalancerName, 'taskmanager-$ENVIRONMENT')].DNSName" \
       --output text)
   
   if [ -n "$ALB_DNS" ]; then
       # Test application health
       for i in {1..10}; do
           if curl -f -s "http://$ALB_DNS/health" | jq -e '.status == "healthy"'; then
               echo "✅ Rollback verification successful"
               break
           else
               echo "⏳ Waiting for application to be healthy... ($i/10)"
               sleep 30
           fi
       done
   fi
   
   # Record rollback in DynamoDB
   aws dynamodb put-item \
       --table-name "taskmanager-rollbacks" \
       --item '{
           "rollback_id": {"S": "'$(date +%s)'"},
           "environment": {"S": "'$ENVIRONMENT'"},
           "target_version": {"S": "'$TARGET_VERSION'"},
           "rolled_back_at": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"},
           "rolled_back_by": {"S": "'$USER'"},
           "checkpoint_file": {"S": "'$CHECKPOINT_FILE'"}
       }'
   
   echo "Rollback completed at: $(date)"
   ```

2. **Create rollback tracking table:**
   ```bash
   aws dynamodb create-table \
       --table-name "taskmanager-rollbacks" \
       --attribute-definitions AttributeName=rollback_id,AttributeType=S \
       --key-schema AttributeName=rollback_id,KeyType=HASH \
       --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
       --region us-east-1
   ```

3. **Make rollback script executable:**
   ```bash
   chmod +x scripts/rollback-environment.sh
   ```

### ✅ Verification

1. **Test disaster recovery:**
   ```bash
   # Test application failure scenario
   ./scripts/disaster-recovery.sh dev app-failure
   ```

2. **Test backup procedures:**
   ```bash
   ./scripts/backup-all-environments.sh
   ```

3. **Test rollback procedures:**
   ```bash
   # Test rollback (use actual version)
   ./scripts/rollback-environment.sh dev previous-version
   ```

---

## Summary

In this final lab, you have successfully:

✅ **Created multi-environment deployment architecture:**
- Deployed staging and production environments with proper isolation
- Configured environment-specific variables and scaling parameters
- Set up Terraform state management with backend configuration

✅ **Implemented environment promotion workflows:**
- Created automated promotion pipeline with validation
- Set up promotion tracking and audit trails
- Implemented approval processes for production deployments

✅ **Set up cross-environment monitoring:**
- Created comprehensive cross-environment dashboard
- Implemented environment comparison and health check tools
- Set up automated monitoring and alerting across all environments

✅ **Established disaster recovery procedures:**
- Created comprehensive disaster recovery plan
- Implemented automated backup procedures
- Set up rollback procedures with checkpoint management

✅ **Completed full multi-environment deployment system:**
- Three fully functional environments (dev, staging, prod)
- Complete CI/CD pipeline with automated testing and deployment
- Comprehensive monitoring, logging, and alerting
- Disaster recovery and business continuity procedures

## Final Architecture

Your completed multi-environment deployment system includes:

- **Development Environment**: Rapid iteration and testing
- **Staging Environment**: Pre-production validation and testing
- **Production Environment**: High-availability production workloads
- **CI/CD Pipeline**: Automated testing, building, and deployment
- **Monitoring System**: Comprehensive observability and alerting
- **Disaster Recovery**: Backup and recovery procedures

## Next Steps

Your multi-environment deployment system is now complete and production-ready. Consider these enhancements:

1. **Security Hardening**: Implement additional security measures
2. **Performance Optimization**: Fine-tune for better performance
3. **Cost Optimization**: Implement cost monitoring and optimization
4. **Compliance**: Add compliance monitoring and reporting
5. **Advanced Features**: Consider blue-green deployments, canary releases

## Troubleshooting

### Common Issues

**Issue:** Environment deployment fails
**Solution:**
- Check Terraform state consistency
- Verify AWS service limits
- Review IAM permissions

**Issue:** Promotion workflow fails
**Solution:**
- Check GitHub environment protection rules
- Verify CI/CD pipeline configuration
- Review promotion validation tests

**Issue:** Monitoring data missing
**Solution:**
- Check CloudWatch Agent configuration
- Verify metric namespaces and dimensions
- Review log group permissions

### Additional Resources

- [AWS Multi-Environment Best Practices](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/)
- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/)
- [CI/CD Pipeline Security](https://docs.github.com/en/actions/security-guides)

---

**🎉 Congratulations!** You have successfully completed all 7 labs and built a comprehensive multi-environment deployment system for your web application. Your system is now production-ready with proper monitoring, disaster recovery, and operational procedures.

**Your achievement includes:**
- ✅ Complete Infrastructure as Code implementation
- ✅ Automated CI/CD pipeline with testing and security scanning
- ✅ Multi-environment deployment with proper isolation
- ✅ Comprehensive monitoring, logging, and alerting
- ✅ Disaster recovery and business continuity procedures
- ✅ Production-ready scalable architecture

This completes the Multi-Environment Web App Deployment lab series!