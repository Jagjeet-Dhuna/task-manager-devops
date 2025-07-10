# Lab 02: Infrastructure Foundation with Terraform

## Overview

In this lab, you will create the foundational infrastructure for your multi-environment deployment using Terraform. You'll design reusable modules, implement network architecture, configure security groups, and deploy the infrastructure to AWS.

## Objectives

After completing this lab, you will be able to:
- Design and implement Terraform module architecture
- Create VPC with public and private subnets across multiple availability zones
- Configure security groups following security best practices
- Deploy infrastructure using Terraform commands
- Validate and troubleshoot infrastructure deployment

## Prerequisites

- Completed Lab 01 (Environment Setup and Application Containerization)
- AWS CLI configured with appropriate credentials
- Terraform installed and verified
- Basic understanding of AWS networking concepts

## Duration

**Estimated Time:** 90 minutes

---

## Exercise 1: Design Terraform Module Architecture

### Task 1: Create Project Structure

1. **Create Terraform directory structure:**
   ```bash
   # From your project root directory
   mkdir -p terraform/modules/{vpc,security-groups,ec2,rds,alb,monitoring}
   mkdir -p terraform/environments/{dev,staging,prod}
   mkdir -p terraform/global
   ```

2. **Verify directory structure:**
   ```bash
   tree terraform/
   ```
   
   **Expected output:**
   ```
   terraform/
   ├── environments/
   │   ├── dev/
   │   ├── staging/
   │   └── prod/
   ├── global/
   └── modules/
       ├── vpc/
       ├── security-groups/
       ├── ec2/
       ├── rds/
       ├── alb/
       └── monitoring/
   ```

### Task 2: Create Terraform Configuration Standards

1. **Create `terraform/modules/README.md`:**
   ```markdown
   # Terraform Modules
   
   This directory contains reusable Terraform modules for infrastructure components.
   
   ## Module Standards
   
   Each module should include:
   - `main.tf` - Primary resource definitions
   - `variables.tf` - Input variables
   - `outputs.tf` - Output values
   - `versions.tf` - Provider version constraints
   - `README.md` - Module documentation
   
   ## Usage
   
   Modules are called from environment-specific configurations in `../environments/`.
   ```

2. **Create global versions file `terraform/global/versions.tf`:**
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
   ```

### ✅ Verification

1. **Check directory structure:**
   ```bash
   find terraform/ -type d | sort
   ```
   Should show all created directories.

2. **Validate Terraform syntax:**
   ```bash
   cd terraform/global
   terraform fmt -check
   terraform validate
   ```

---

## Exercise 2: Create VPC and Networking Components

### Task 1: Create VPC Module

1. **Create `terraform/modules/vpc/versions.tf`:**
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
   ```

2. **Create `terraform/modules/vpc/variables.tf`:**
   ```hcl
   variable "environment" {
     description = "Environment name (e.g., dev, staging, prod)"
     type        = string
     validation {
       condition     = can(regex("^(dev|staging|prod)$", var.environment))
       error_message = "Environment must be dev, staging, or prod."
     }
   }
   
   variable "vpc_cidr" {
     description = "CIDR block for VPC"
     type        = string
     validation {
       condition     = can(cidrhost(var.vpc_cidr, 0))
       error_message = "VPC CIDR must be a valid IPv4 CIDR block."
     }
   }
   
   variable "public_subnet_cidrs" {
     description = "CIDR blocks for public subnets"
     type        = list(string)
     validation {
       condition     = length(var.public_subnet_cidrs) >= 2
       error_message = "At least 2 public subnets required for high availability."
     }
   }
   
   variable "private_subnet_cidrs" {
     description = "CIDR blocks for private subnets"
     type        = list(string)
     validation {
       condition     = length(var.private_subnet_cidrs) >= 2
       error_message = "At least 2 private subnets required for high availability."
     }
   }
   
   variable "availability_zones" {
     description = "List of availability zones"
     type        = list(string)
     validation {
       condition     = length(var.availability_zones) >= 2
       error_message = "At least 2 availability zones required for high availability."
     }
   }
   
   variable "enable_nat_gateway" {
     description = "Enable NAT Gateway for private subnets"
     type        = bool
     default     = true
   }
   
   variable "enable_vpn_gateway" {
     description = "Enable VPN Gateway for the VPC"
     type        = bool
     default     = false
   }
   
   variable "tags" {
     description = "Additional tags to apply to all resources"
     type        = map(string)
     default     = {}
   }
   ```

3. **Create `terraform/modules/vpc/main.tf`:**
   ```hcl
   # Data source for current AWS region
   data "aws_region" "current" {}
   
   # Data source for caller identity
   data "aws_caller_identity" "current" {}
   
   # Local values for consistent tagging
   locals {
     common_tags = merge(var.tags, {
       Environment = var.environment
       Project     = "TaskManager"
       ManagedBy   = "Terraform"
       Owner       = data.aws_caller_identity.current.user_id
     })
   }
   
   # VPC
   resource "aws_vpc" "main" {
     cidr_block           = var.vpc_cidr
     enable_dns_hostnames = true
     enable_dns_support   = true
     
     tags = merge(local.common_tags, {
       Name = "${var.environment}-vpc"
     })
   }
   
   # Internet Gateway
   resource "aws_internet_gateway" "main" {
     vpc_id = aws_vpc.main.id
     
     tags = merge(local.common_tags, {
       Name = "${var.environment}-igw"
     })
   }
   
   # Public Subnets
   resource "aws_subnet" "public" {
     count                   = length(var.public_subnet_cidrs)
     vpc_id                  = aws_vpc.main.id
     cidr_block              = var.public_subnet_cidrs[count.index]
     availability_zone       = var.availability_zones[count.index]
     map_public_ip_on_launch = true
     
     tags = merge(local.common_tags, {
       Name = "${var.environment}-public-subnet-${count.index + 1}"
       Type = "Public"
       AZ   = var.availability_zones[count.index]
     })
   }
   
   # Private Subnets
   resource "aws_subnet" "private" {
     count             = length(var.private_subnet_cidrs)
     vpc_id            = aws_vpc.main.id
     cidr_block        = var.private_subnet_cidrs[count.index]
     availability_zone = var.availability_zones[count.index]
     
     tags = merge(local.common_tags, {
       Name = "${var.environment}-private-subnet-${count.index + 1}"
       Type = "Private"
       AZ   = var.availability_zones[count.index]
     })
   }
   
   # Elastic IPs for NAT Gateways
   resource "aws_eip" "nat" {
     count  = var.enable_nat_gateway ? length(var.public_subnet_cidrs) : 0
     domain = "vpc"
     
     tags = merge(local.common_tags, {
       Name = "${var.environment}-nat-eip-${count.index + 1}"
     })
     
     depends_on = [aws_internet_gateway.main]
   }
   
   # NAT Gateways
   resource "aws_nat_gateway" "main" {
     count         = var.enable_nat_gateway ? length(var.public_subnet_cidrs) : 0
     allocation_id = aws_eip.nat[count.index].id
     subnet_id     = aws_subnet.public[count.index].id
     
     tags = merge(local.common_tags, {
       Name = "${var.environment}-nat-gateway-${count.index + 1}"
     })
     
     depends_on = [aws_internet_gateway.main]
   }
   
   # Route Table for Public Subnets
   resource "aws_route_table" "public" {
     vpc_id = aws_vpc.main.id
     
     route {
       cidr_block = "0.0.0.0/0"
       gateway_id = aws_internet_gateway.main.id
     }
     
     tags = merge(local.common_tags, {
       Name = "${var.environment}-public-rt"
       Type = "Public"
     })
   }
   
   # Route Table Associations for Public Subnets
   resource "aws_route_table_association" "public" {
     count          = length(aws_subnet.public)
     subnet_id      = aws_subnet.public[count.index].id
     route_table_id = aws_route_table.public.id
   }
   
   # Route Tables for Private Subnets
   resource "aws_route_table" "private" {
     count  = length(var.private_subnet_cidrs)
     vpc_id = aws_vpc.main.id
     
     dynamic "route" {
       for_each = var.enable_nat_gateway ? [1] : []
       content {
         cidr_block     = "0.0.0.0/0"
         nat_gateway_id = aws_nat_gateway.main[count.index].id
       }
     }
     
     tags = merge(local.common_tags, {
       Name = "${var.environment}-private-rt-${count.index + 1}"
       Type = "Private"
     })
   }
   
   # Route Table Associations for Private Subnets
   resource "aws_route_table_association" "private" {
     count          = length(aws_subnet.private)
     subnet_id      = aws_subnet.private[count.index].id
     route_table_id = aws_route_table.private[count.index].id
   }
   
   # VPC Flow Logs
   resource "aws_flow_log" "vpc_flow_log" {
     iam_role_arn    = aws_iam_role.flow_log.arn
     log_destination = aws_cloudwatch_log_group.vpc_flow_log.arn
     traffic_type    = "ALL"
     vpc_id          = aws_vpc.main.id
     
     tags = merge(local.common_tags, {
       Name = "${var.environment}-vpc-flow-logs"
     })
   }
   
   # CloudWatch Log Group for VPC Flow Logs
   resource "aws_cloudwatch_log_group" "vpc_flow_log" {
     name              = "/aws/vpc/${var.environment}/flowlogs"
     retention_in_days = 14
     
     tags = local.common_tags
   }
   
   # IAM Role for VPC Flow Logs
   resource "aws_iam_role" "flow_log" {
     name = "${var.environment}-vpc-flow-logs-role"
     
     assume_role_policy = jsonencode({
       Version = "2012-10-17"
       Statement = [
         {
           Action = "sts:AssumeRole"
           Effect = "Allow"
           Principal = {
             Service = "vpc-flow-logs.amazonaws.com"
           }
         }
       ]
     })
     
     tags = local.common_tags
   }
   
   # IAM Policy for VPC Flow Logs
   resource "aws_iam_role_policy" "flow_log" {
     name = "${var.environment}-vpc-flow-logs-policy"
     role = aws_iam_role.flow_log.id
     
     policy = jsonencode({
       Version = "2012-10-17"
       Statement = [
         {
           Action = [
             "logs:CreateLogGroup",
             "logs:CreateLogStream",
             "logs:PutLogEvents",
             "logs:DescribeLogGroups",
             "logs:DescribeLogStreams"
           ]
           Effect   = "Allow"
           Resource = "*"
         }
       ]
     })
   }
   ```

4. **Create `terraform/modules/vpc/outputs.tf`:**
   ```hcl
   output "vpc_id" {
     description = "ID of the VPC"
     value       = aws_vpc.main.id
   }
   
   output "vpc_cidr_block" {
     description = "CIDR block of the VPC"
     value       = aws_vpc.main.cidr_block
   }
   
   output "public_subnet_ids" {
     description = "IDs of the public subnets"
     value       = aws_subnet.public[*].id
   }
   
   output "private_subnet_ids" {
     description = "IDs of the private subnets"
     value       = aws_subnet.private[*].id
   }
   
   output "public_subnet_cidrs" {
     description = "CIDR blocks of the public subnets"
     value       = aws_subnet.public[*].cidr_block
   }
   
   output "private_subnet_cidrs" {
     description = "CIDR blocks of the private subnets"
     value       = aws_subnet.private[*].cidr_block
   }
   
   output "internet_gateway_id" {
     description = "ID of the Internet Gateway"
     value       = aws_internet_gateway.main.id
   }
   
   output "nat_gateway_ids" {
     description = "IDs of the NAT Gateways"
     value       = aws_nat_gateway.main[*].id
   }
   
   output "nat_gateway_public_ips" {
     description = "Public IPs of the NAT Gateways"
     value       = aws_eip.nat[*].public_ip
   }
   
   output "public_route_table_id" {
     description = "ID of the public route table"
     value       = aws_route_table.public.id
   }
   
   output "private_route_table_ids" {
     description = "IDs of the private route tables"
     value       = aws_route_table.private[*].id
   }
   
   output "availability_zones" {
     description = "List of availability zones"
     value       = var.availability_zones
   }
   
   output "vpc_flow_log_id" {
     description = "ID of the VPC Flow Log"
     value       = aws_flow_log.vpc_flow_log.id
   }
   ```

### ✅ Verification

1. **Validate VPC module:**
   ```bash
   cd terraform/modules/vpc
   terraform fmt
   terraform validate
   ```
   
   **Expected output:**
   ```
   Success! The configuration is valid.
   ```

---

## Exercise 3: Implement Security Groups and Access Control

### Task 1: Create Security Groups Module

1. **Create `terraform/modules/security-groups/versions.tf`:**
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
   ```

2. **Create `terraform/modules/security-groups/variables.tf`:**
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
   
   variable "allowed_cidr_blocks" {
     description = "List of CIDR blocks allowed to access the application"
     type        = list(string)
     default     = ["0.0.0.0/0"]
   }
   
   variable "tags" {
     description = "Additional tags to apply to all resources"
     type        = map(string)
     default     = {}
   }
   ```

3. **Create `terraform/modules/security-groups/main.tf`:**
   ```hcl
   # Data source for caller identity
   data "aws_caller_identity" "current" {}
   
   # Local values for consistent tagging
   locals {
     common_tags = merge(var.tags, {
       Environment = var.environment
       Project     = "TaskManager"
       ManagedBy   = "Terraform"
       Owner       = data.aws_caller_identity.current.user_id
     })
   }
   
   # Security Group for Application Load Balancer
   resource "aws_security_group" "alb" {
     name        = "${var.environment}-alb-sg"
     description = "Security group for Application Load Balancer"
     vpc_id      = var.vpc_id
     
     # HTTP ingress
     ingress {
       description = "HTTP from internet"
       from_port   = 80
       to_port     = 80
       protocol    = "tcp"
       cidr_blocks = var.allowed_cidr_blocks
     }
     
     # HTTPS ingress
     ingress {
       description = "HTTPS from internet"
       from_port   = 443
       to_port     = 443
       protocol    = "tcp"
       cidr_blocks = var.allowed_cidr_blocks
     }
     
     # All outbound traffic
     egress {
       description = "All outbound traffic"
       from_port   = 0
       to_port     = 0
       protocol    = "-1"
       cidr_blocks = ["0.0.0.0/0"]
     }
     
     tags = merge(local.common_tags, {
       Name = "${var.environment}-alb-sg"
       Type = "LoadBalancer"
     })
   }
   
   # Security Group for Web Servers
   resource "aws_security_group" "web" {
     name        = "${var.environment}-web-sg"
     description = "Security group for web servers"
     vpc_id      = var.vpc_id
     
     # Application port from ALB
     ingress {
       description     = "Application traffic from ALB"
       from_port       = 5000
       to_port         = 5000
       protocol        = "tcp"
       security_groups = [aws_security_group.alb.id]
     }
     
     # SSH from within VPC (for troubleshooting)
     ingress {
       description = "SSH from VPC"
       from_port   = 22
       to_port     = 22
       protocol    = "tcp"
       cidr_blocks = [var.vpc_cidr_block]
     }
     
     # All outbound traffic
     egress {
       description = "All outbound traffic"
       from_port   = 0
       to_port     = 0
       protocol    = "-1"
       cidr_blocks = ["0.0.0.0/0"]
     }
     
     tags = merge(local.common_tags, {
       Name = "${var.environment}-web-sg"
       Type = "WebServer"
     })
   }
   
   # Security Group for Database
   resource "aws_security_group" "database" {
     name        = "${var.environment}-database-sg"
     description = "Security group for database servers"
     vpc_id      = var.vpc_id
     
     # PostgreSQL from web servers
     ingress {
       description     = "PostgreSQL from web servers"
       from_port       = 5432
       to_port         = 5432
       protocol        = "tcp"
       security_groups = [aws_security_group.web.id]
     }
     
     # No outbound rules needed for database
     tags = merge(local.common_tags, {
       Name = "${var.environment}-database-sg"
       Type = "Database"
     })
   }
   
   # Security Group for Bastion Host (optional)
   resource "aws_security_group" "bastion" {
     name        = "${var.environment}-bastion-sg"
     description = "Security group for bastion host"
     vpc_id      = var.vpc_id
     
     # SSH from allowed CIDR blocks
     ingress {
       description = "SSH from allowed IPs"
       from_port   = 22
       to_port     = 22
       protocol    = "tcp"
       cidr_blocks = var.allowed_cidr_blocks
     }
     
     # Outbound to VPC for SSH forwarding
     egress {
       description = "SSH to VPC"
       from_port   = 22
       to_port     = 22
       protocol    = "tcp"
       cidr_blocks = [var.vpc_cidr_block]
     }
     
     tags = merge(local.common_tags, {
       Name = "${var.environment}-bastion-sg"
       Type = "Bastion"
     })
   }
   
   # Security Group for VPC Endpoints (optional)
   resource "aws_security_group" "vpc_endpoints" {
     name        = "${var.environment}-vpc-endpoints-sg"
     description = "Security group for VPC endpoints"
     vpc_id      = var.vpc_id
     
     # HTTPS from VPC
     ingress {
       description = "HTTPS from VPC"
       from_port   = 443
       to_port     = 443
       protocol    = "tcp"
       cidr_blocks = [var.vpc_cidr_block]
     }
     
     tags = merge(local.common_tags, {
       Name = "${var.environment}-vpc-endpoints-sg"
       Type = "VPCEndpoint"
     })
   }
   ```

4. **Create `terraform/modules/security-groups/outputs.tf`:**
   ```hcl
   output "alb_security_group_id" {
     description = "ID of the ALB security group"
     value       = aws_security_group.alb.id
   }
   
   output "web_security_group_id" {
     description = "ID of the web security group"
     value       = aws_security_group.web.id
   }
   
   output "database_security_group_id" {
     description = "ID of the database security group"
     value       = aws_security_group.database.id
   }
   
   output "bastion_security_group_id" {
     description = "ID of the bastion security group"
     value       = aws_security_group.bastion.id
   }
   
   output "vpc_endpoints_security_group_id" {
     description = "ID of the VPC endpoints security group"
     value       = aws_security_group.vpc_endpoints.id
   }
   
   output "alb_security_group_arn" {
     description = "ARN of the ALB security group"
     value       = aws_security_group.alb.arn
   }
   
   output "web_security_group_arn" {
     description = "ARN of the web security group"
     value       = aws_security_group.web.arn
   }
   
   output "database_security_group_arn" {
     description = "ARN of the database security group"
     value       = aws_security_group.database.arn
   }
   ```

### ✅ Verification

1. **Validate security groups module:**
   ```bash
   cd terraform/modules/security-groups
   terraform fmt
   terraform validate
   ```

---

## Exercise 4: Deploy and Validate Infrastructure

### Task 1: Create Development Environment Configuration

1. **Create `terraform/environments/dev/versions.tf`:**
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
   ```

2. **Create `terraform/environments/dev/variables.tf`:**
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
   
   variable "project_name" {
     description = "Project name"
     type        = string
     default     = "TaskManager"
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
   
   variable "allowed_cidr_blocks" {
     description = "CIDR blocks allowed to access the application"
     type        = list(string)
     default     = ["0.0.0.0/0"]
   }
   ```

3. **Create `terraform/environments/dev/main.tf`:**
   ```hcl
   # Configure the AWS Provider
   provider "aws" {
     region = var.aws_region
     
     default_tags {
       tags = {
         Environment = var.environment
         Project     = var.project_name
         ManagedBy   = "Terraform"
       }
     }
   }
   
   # VPC Module
   module "vpc" {
     source = "../../modules/vpc"
     
     environment            = var.environment
     vpc_cidr              = var.vpc_cidr
     public_subnet_cidrs   = var.public_subnet_cidrs
     private_subnet_cidrs  = var.private_subnet_cidrs
     availability_zones    = var.availability_zones
     enable_nat_gateway    = true
     enable_vpn_gateway    = false
     
     tags = {
       Project = var.project_name
     }
   }
   
   # Security Groups Module
   module "security_groups" {
     source = "../../modules/security-groups"
     
     environment        = var.environment
     vpc_id            = module.vpc.vpc_id
     vpc_cidr_block    = module.vpc.vpc_cidr_block
     allowed_cidr_blocks = var.allowed_cidr_blocks
     
     tags = {
       Project = var.project_name
     }
   }
   ```

4. **Create `terraform/environments/dev/outputs.tf`:**
   ```hcl
   # VPC Outputs
   output "vpc_id" {
     description = "ID of the VPC"
     value       = module.vpc.vpc_id
   }
   
   output "vpc_cidr_block" {
     description = "CIDR block of the VPC"
     value       = module.vpc.vpc_cidr_block
   }
   
   output "public_subnet_ids" {
     description = "IDs of the public subnets"
     value       = module.vpc.public_subnet_ids
   }
   
   output "private_subnet_ids" {
     description = "IDs of the private subnets"
     value       = module.vpc.private_subnet_ids
   }
   
   output "nat_gateway_public_ips" {
     description = "Public IPs of the NAT Gateways"
     value       = module.vpc.nat_gateway_public_ips
   }
   
   # Security Group Outputs
   output "alb_security_group_id" {
     description = "ID of the ALB security group"
     value       = module.security_groups.alb_security_group_id
   }
   
   output "web_security_group_id" {
     description = "ID of the web security group"
     value       = module.security_groups.web_security_group_id
   }
   
   output "database_security_group_id" {
     description = "ID of the database security group"
     value       = module.security_groups.database_security_group_id
   }
   
   # Environment Information
   output "environment" {
     description = "Environment name"
     value       = var.environment
   }
   
   output "aws_region" {
     description = "AWS region"
     value       = var.aws_region
   }
   
   output "availability_zones" {
     description = "List of availability zones"
     value       = var.availability_zones
   }
   ```

### Task 2: Initialize and Deploy Infrastructure

1. **Initialize Terraform:**
   ```bash
   cd terraform/environments/dev
   terraform init
   ```
   
   **Expected output:**
   ```
   Initializing modules...
   - vpc in ../../modules/vpc
   - security_groups in ../../modules/security-groups
   
   Initializing the backend...
   
   Initializing provider plugins...
   - Finding hashicorp/aws versions matching "~> 5.0"...
   - Installing hashicorp/aws v5.x.x...
   
   Terraform has been successfully initialized!
   ```

2. **Format and validate configuration:**
   ```bash
   terraform fmt -recursive
   terraform validate
   ```

3. **Plan infrastructure deployment:**
   ```bash
   terraform plan -out=tfplan
   ```
   
   **Review the plan output carefully. You should see:**
   - 1 VPC to be created
   - 4 subnets (2 public, 2 private)
   - 1 Internet Gateway
   - 2 NAT Gateways
   - 2 Elastic IPs
   - 5 Route Tables
   - 5 Security Groups
   - Various IAM roles and policies
   - CloudWatch log group
   - VPC Flow Logs

4. **Apply infrastructure deployment:**
   ```bash
   terraform apply tfplan
   ```
   
   **Expected output:**
   ```
   Apply complete! Resources: 25 added, 0 changed, 0 destroyed.
   
   Outputs:
   
   alb_security_group_id = "sg-xxxxxxxxx"
   aws_region = "us-east-1"
   database_security_group_id = "sg-xxxxxxxxx"
   environment = "dev"
   nat_gateway_public_ips = [
     "x.x.x.x",
     "y.y.y.y",
   ]
   private_subnet_ids = [
     "subnet-xxxxxxxxx",
     "subnet-xxxxxxxxx",
   ]
   public_subnet_ids = [
     "subnet-xxxxxxxxx",
     "subnet-xxxxxxxxx",
   ]
   vpc_cidr_block = "10.0.0.0/16"
   vpc_id = "vpc-xxxxxxxxx"
   web_security_group_id = "sg-xxxxxxxxx"
   ```

### Task 3: Validate Infrastructure Deployment

1. **Verify VPC creation:**
   ```bash
   aws ec2 describe-vpcs --filters "Name=tag:Environment,Values=dev" --query 'Vpcs[*].[VpcId,CidrBlock,State]' --output table
   ```
   
   **Expected output:**
   ```
   ---------------------------------
   |         DescribeVpcs         |
   +-------------+----------------+
   |  vpc-xxxxx  |  10.0.0.0/16  |  available
   +-------------+----------------+
   ```

2. **Verify subnets creation:**
   ```bash
   aws ec2 describe-subnets --filters "Name=tag:Environment,Values=dev" --query 'Subnets[*].[SubnetId,CidrBlock,AvailabilityZone,Tags[?Key==`Type`].Value|[0]]' --output table
   ```

3. **Verify security groups:**
   ```bash
   aws ec2 describe-security-groups --filters "Name=tag:Environment,Values=dev" --query 'SecurityGroups[*].[GroupId,GroupName,Description]' --output table
   ```

4. **Test connectivity (optional):**
   ```bash
   # Test NAT Gateway connectivity
   aws ec2 describe-nat-gateways --filter "Name=tag:Environment,Values=dev" --query 'NatGateways[*].[NatGatewayId,State,SubnetId]' --output table
   ```

### ✅ Verification

1. **Infrastructure deployed successfully:**
   ```bash
   terraform output
   ```
   Should show all expected outputs.

2. **AWS resources created:**
   ```bash
   aws ec2 describe-vpcs --filters "Name=tag:Environment,Values=dev"
   ```
   Should return VPC information.

3. **Security groups configured:**
   ```bash
   aws ec2 describe-security-groups --filters "Name=tag:Environment,Values=dev"
   ```
   Should show 5 security groups.

---

## Exercise 5: Create Environment-Specific Configurations

### Task 1: Create Staging Environment

1. **Copy development environment:**
   ```bash
   cp -r terraform/environments/dev terraform/environments/staging
   ```

2. **Update `terraform/environments/staging/variables.tf`:**
   ```hcl
   # Change default values for staging
   variable "environment" {
     description = "Environment name"
     type        = string
     default     = "staging"
   }
   
   variable "vpc_cidr" {
     description = "CIDR block for VPC"
     type        = string
     default     = "10.1.0.0/16"  # Different CIDR for staging
   }
   
   variable "public_subnet_cidrs" {
     description = "CIDR blocks for public subnets"
     type        = list(string)
     default     = ["10.1.1.0/24", "10.1.2.0/24"]
   }
   
   variable "private_subnet_cidrs" {
     description = "CIDR blocks for private subnets"
     type        = list(string)
     default     = ["10.1.11.0/24", "10.1.12.0/24"]
   }
   
   # Keep other variables the same
   ```

### Task 2: Create Production Environment

1. **Copy development environment:**
   ```bash
   cp -r terraform/environments/dev terraform/environments/prod
   ```

2. **Update `terraform/environments/prod/variables.tf`:**
   ```hcl
   # Change default values for production
   variable "environment" {
     description = "Environment name"
     type        = string
     default     = "prod"
   }
   
   variable "vpc_cidr" {
     description = "CIDR block for VPC"
     type        = string
     default     = "10.2.0.0/16"  # Different CIDR for production
   }
   
   variable "public_subnet_cidrs" {
     description = "CIDR blocks for public subnets"
     type        = list(string)
     default     = ["10.2.1.0/24", "10.2.2.0/24"]
   }
   
   variable "private_subnet_cidrs" {
     description = "CIDR blocks for private subnets"
     type        = list(string)
     default     = ["10.2.11.0/24", "10.2.12.0/24"]
   }
   
   # More restrictive access for production
   variable "allowed_cidr_blocks" {
     description = "CIDR blocks allowed to access the application"
     type        = list(string)
     default     = ["0.0.0.0/0"]  # Should be restricted in real production
   }
   ```

### Task 3: Test Environment Configurations

1. **Validate staging configuration:**
   ```bash
   cd terraform/environments/staging
   terraform init
   terraform validate
   terraform plan
   ```

2. **Validate production configuration:**
   ```bash
   cd terraform/environments/prod
   terraform init
   terraform validate
   terraform plan
   ```

### ✅ Verification

1. **All environments validate successfully:**
   ```bash
   # From each environment directory
   terraform validate
   ```

2. **Different CIDR blocks configured:**
   ```bash
   # Check each environment's variables
   grep -r "vpc_cidr" terraform/environments/*/variables.tf
   ```

---

## Summary

In this lab, you have successfully:

✅ **Designed Terraform module architecture:**
- Created reusable module structure
- Implemented consistent naming and tagging standards
- Established version constraints and provider configurations

✅ **Created VPC and networking infrastructure:**
- Deployed VPC with proper CIDR allocation
- Configured public and private subnets across availability zones
- Implemented NAT Gateways for private subnet internet access
- Set up VPC Flow Logs for security monitoring

✅ **Implemented security groups:**
- Created security groups following least-privilege principles
- Configured proper ingress and egress rules
- Implemented layered security architecture

✅ **Deployed and validated infrastructure:**
- Successfully deployed infrastructure to AWS
- Verified all components are working correctly
- Tested connectivity and security group rules

✅ **Created environment-specific configurations:**
- Set up dev, staging, and production environments
- Configured environment-specific CIDR blocks
- Prepared for multi-environment deployments

## Next Steps

Your networking foundation is now ready for application deployment. In the next lab, you will:

- Create RDS PostgreSQL database instances
- Configure database security and backup strategies
- Implement database parameter groups and monitoring
- Test database connectivity from application subnets

## Troubleshooting

### Common Issues

**Issue:** Terraform init fails with provider errors
**Solution:** 
- Check internet connectivity
- Verify AWS credentials are configured
- Ensure Terraform version is compatible

**Issue:** Resource creation fails with permission errors
**Solution:**
- Verify AWS IAM permissions
- Check AWS CLI configuration: `aws sts get-caller-identity`
- Ensure proper AWS region is configured

**Issue:** CIDR block conflicts
**Solution:**
- Verify CIDR blocks don't overlap with existing VPCs
- Check availability zone availability in your region
- Ensure subnets fit within VPC CIDR block

**Issue:** Security group rules not working
**Solution:**
- Check security group references vs CIDR blocks
- Verify ingress/egress rules are properly configured
- Test with more permissive rules first, then restrict

### Additional Resources

- [AWS VPC Documentation](https://docs.aws.amazon.com/vpc/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/)
- [AWS Security Groups Best Practices](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html)
- [Terraform Module Development](https://www.terraform.io/docs/modules/index.html)

---

**🎉 Congratulations!** You have successfully completed Lab 02. Your infrastructure foundation is now deployed and ready for database and application components.

**Next:** [Lab 03: Database Infrastructure and Management](./03-database-infrastructure-management.md)