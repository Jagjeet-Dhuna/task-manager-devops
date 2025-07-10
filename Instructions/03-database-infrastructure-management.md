# Lab 03: Database Infrastructure and Management

## Overview

In this lab, you will create a secure, scalable PostgreSQL database infrastructure using AWS RDS. You'll implement database security best practices, configure backup and monitoring, and establish proper connectivity patterns for your multi-environment architecture.

## Objectives

After completing this lab, you will be able to:
- Create RDS PostgreSQL instances with proper security configuration
- Implement database subnet groups and parameter groups
- Configure automated backups and monitoring
- Set up database connectivity and performance optimization
- Create database initialization and migration scripts

## Prerequisites

- Completed Lab 02 (Infrastructure Foundation with Terraform)
- Understanding of database fundamentals
- Basic knowledge of PostgreSQL administration
- Terraform modules from previous lab

## Duration

**Estimated Time:** 45 minutes

---

## Exercise 1: Create RDS Terraform Module

### Task 1: Create RDS Module Structure

1. **Create RDS module directory:**
   ```bash
   mkdir -p terraform/modules/rds
   cd terraform/modules/rds
   ```

2. **Create `main.tf` for RDS resources:**
   ```hcl
   # DB Subnet Group
   resource "aws_db_subnet_group" "main" {
     name       = "${var.project_name}-${var.environment}-db-subnet-group"
     subnet_ids = var.database_subnets
   
     tags = {
       Name = "${var.project_name}-${var.environment}-db-subnet-group"
       Environment = var.environment
     }
   }
   
   # DB Parameter Group
   resource "aws_db_parameter_group" "main" {
     family = "postgres13"
     name   = "${var.project_name}-${var.environment}-db-params"
   
     parameter {
       name  = "shared_preload_libraries"
       value = "pg_stat_statements"
     }
   
     parameter {
       name  = "log_statement"
       value = "all"
     }
   
     parameter {
       name  = "log_min_duration_statement"
       value = "1000"
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-db-params"
       Environment = var.environment
     }
   }
   
   # RDS Instance
   resource "aws_db_instance" "main" {
     identifier = "${var.project_name}-${var.environment}-db"
   
     # Engine Configuration
     engine         = "postgres"
     engine_version = "13.7"
     instance_class = var.instance_class
   
     # Database Configuration
     allocated_storage     = var.allocated_storage
     max_allocated_storage = var.max_allocated_storage
     storage_type         = "gp2"
     storage_encrypted    = true
   
     # Database Credentials
     db_name  = var.database_name
     username = var.database_username
     password = var.database_password
   
     # Network Configuration
     db_subnet_group_name   = aws_db_subnet_group.main.name
     vpc_security_group_ids = var.security_group_ids
     publicly_accessible    = false
   
     # Backup Configuration
     backup_retention_period = var.backup_retention_period
     backup_window          = var.backup_window
     maintenance_window     = var.maintenance_window
   
     # Monitoring
     monitoring_interval = 60
     monitoring_role_arn = aws_iam_role.rds_monitoring.arn
   
     # Parameter Group
     parameter_group_name = aws_db_parameter_group.main.name
   
     # Deletion Protection
     deletion_protection = var.deletion_protection
     skip_final_snapshot = var.skip_final_snapshot
   
     # Performance Insights
     performance_insights_enabled = true
     performance_insights_retention_period = 7
   
     tags = {
       Name = "${var.project_name}-${var.environment}-db"
       Environment = var.environment
     }
   }
   
   # IAM Role for RDS Enhanced Monitoring
   resource "aws_iam_role" "rds_monitoring" {
     name = "${var.project_name}-${var.environment}-rds-monitoring"
   
     assume_role_policy = jsonencode({
       Version = "2012-10-17"
       Statement = [
         {
           Action = "sts:AssumeRole"
           Effect = "Allow"
           Principal = {
             Service = "monitoring.rds.amazonaws.com"
           }
         }
       ]
     })
   }
   
   resource "aws_iam_role_policy_attachment" "rds_monitoring" {
     role       = aws_iam_role.rds_monitoring.name
     policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
   }
   ```

3. **Create `variables.tf`:**
   ```hcl
   variable "project_name" {
     description = "Name of the project"
     type        = string
   }
   
   variable "environment" {
     description = "Environment name"
     type        = string
   }
   
   variable "database_subnets" {
     description = "List of subnet IDs for the database"
     type        = list(string)
   }
   
   variable "security_group_ids" {
     description = "List of security group IDs"
     type        = list(string)
   }
   
   variable "instance_class" {
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
   
   variable "database_name" {
     description = "Name of the database"
     type        = string
   }
   
   variable "database_username" {
     description = "Database username"
     type        = string
   }
   
   variable "database_password" {
     description = "Database password"
     type        = string
     sensitive   = true
   }
   
   variable "backup_retention_period" {
     description = "Backup retention period in days"
     type        = number
     default     = 7
   }
   
   variable "backup_window" {
     description = "Backup window"
     type        = string
     default     = "03:00-04:00"
   }
   
   variable "maintenance_window" {
     description = "Maintenance window"
     type        = string
     default     = "sun:04:00-sun:05:00"
   }
   
   variable "deletion_protection" {
     description = "Enable deletion protection"
     type        = bool
     default     = true
   }
   
   variable "skip_final_snapshot" {
     description = "Skip final snapshot on deletion"
     type        = bool
     default     = false
   }
   ```

4. **Create `outputs.tf`:**
   ```hcl
   output "db_instance_id" {
     description = "RDS instance ID"
     value       = aws_db_instance.main.id
   }
   
   output "db_endpoint" {
     description = "RDS instance endpoint"
     value       = aws_db_instance.main.endpoint
   }
   
   output "db_port" {
     description = "RDS instance port"
     value       = aws_db_instance.main.port
   }
   
   output "db_name" {
     description = "Database name"
     value       = aws_db_instance.main.db_name
   }
   
   output "db_username" {
     description = "Database username"
     value       = aws_db_instance.main.username
     sensitive   = true
   }
   
   output "db_subnet_group_name" {
     description = "Database subnet group name"
     value       = aws_db_subnet_group.main.name
   }
   
   output "db_parameter_group_name" {
     description = "Database parameter group name"
     value       = aws_db_parameter_group.main.name
   }
   ```

### Task 2: Create Database Security Group

1. **Update security groups module (`terraform/modules/security-groups/main.tf`):**
   ```hcl
   # Database Security Group
   resource "aws_security_group" "database" {
     name        = "${var.project_name}-${var.environment}-database-sg"
     description = "Security group for database"
     vpc_id      = var.vpc_id
   
     ingress {
       from_port       = 5432
       to_port         = 5432
       protocol        = "tcp"
       security_groups = [aws_security_group.web.id]
       description     = "PostgreSQL from web servers"
     }
   
     egress {
       from_port   = 0
       to_port     = 0
       protocol    = "-1"
       cidr_blocks = ["0.0.0.0/0"]
       description = "All outbound traffic"
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-database-sg"
       Environment = var.environment
     }
   }
   ```

2. **Add database security group output:**
   ```hcl
   output "database_security_group_id" {
     description = "ID of the database security group"
     value       = aws_security_group.database.id
   }
   ```

### ✅ Verification

1. **Validate Terraform configuration:**
   ```bash
   cd terraform/modules/rds
   terraform validate
   ```

2. **Check syntax:**
   ```bash
   terraform fmt -check
   ```

---

## Exercise 2: Configure Database Security and Networking

### Task 1: Create Database Secrets

1. **Create `terraform/modules/secrets/main.tf`:**
   ```hcl
   # Random password for database
   resource "random_password" "db_password" {
     length  = 32
     special = true
   }
   
   # AWS Secrets Manager secret
   resource "aws_secretsmanager_secret" "db_password" {
     name = "${var.project_name}-${var.environment}-db-password"
     description = "Database password for ${var.project_name} ${var.environment}"
   
     tags = {
       Name = "${var.project_name}-${var.environment}-db-password"
       Environment = var.environment
     }
   }
   
   resource "aws_secretsmanager_secret_version" "db_password" {
     secret_id = aws_secretsmanager_secret.db_password.id
     secret_string = jsonencode({
       username = var.database_username
       password = random_password.db_password.result
     })
   }
   ```

2. **Create `terraform/modules/secrets/variables.tf`:**
   ```hcl
   variable "project_name" {
     description = "Name of the project"
     type        = string
   }
   
   variable "environment" {
     description = "Environment name"
     type        = string
   }
   
   variable "database_username" {
     description = "Database username"
     type        = string
   }
   ```

3. **Create `terraform/modules/secrets/outputs.tf`:**
   ```hcl
   output "db_password" {
     description = "Database password"
     value       = random_password.db_password.result
     sensitive   = true
   }
   
   output "db_secret_arn" {
     description = "ARN of the database secret"
     value       = aws_secretsmanager_secret.db_password.arn
   }
   ```

### Task 2: Update VPC Module for Database Subnets

1. **Update `terraform/modules/vpc/main.tf` to add database subnets:**
   ```hcl
   # Database Subnets
   resource "aws_subnet" "database" {
     count = length(var.database_subnet_cidrs)
   
     vpc_id            = aws_vpc.main.id
     cidr_block        = var.database_subnet_cidrs[count.index]
     availability_zone = var.availability_zones[count.index]
   
     tags = {
       Name = "${var.project_name}-${var.environment}-database-subnet-${count.index + 1}"
       Environment = var.environment
       Type = "Database"
     }
   }
   
   # Database Route Table
   resource "aws_route_table" "database" {
     vpc_id = aws_vpc.main.id
   
     tags = {
       Name = "${var.project_name}-${var.environment}-database-rt"
       Environment = var.environment
     }
   }
   
   # Database Route Table Associations
   resource "aws_route_table_association" "database" {
     count = length(aws_subnet.database)
   
     subnet_id      = aws_subnet.database[count.index].id
     route_table_id = aws_route_table.database.id
   }
   ```

2. **Update `terraform/modules/vpc/variables.tf`:**
   ```hcl
   variable "database_subnet_cidrs" {
     description = "CIDR blocks for database subnets"
     type        = list(string)
   }
   ```

3. **Update `terraform/modules/vpc/outputs.tf`:**
   ```hcl
   output "database_subnet_ids" {
     description = "List of database subnet IDs"
     value       = aws_subnet.database[*].id
   }
   ```

### ✅ Verification

1. **Validate updated modules:**
   ```bash
   terraform validate
   ```

2. **Check resource dependencies:**
   ```bash
   terraform graph | dot -Tpng > dependency_graph.png
   ```

---

## Exercise 3: Implement Backup and Monitoring

### Task 1: Create CloudWatch Alarms

1. **Create `terraform/modules/monitoring/database.tf`:**
   ```hcl
   # Database CPU Utilization Alarm
   resource "aws_cloudwatch_metric_alarm" "database_cpu" {
     alarm_name          = "${var.project_name}-${var.environment}-database-cpu"
     comparison_operator = "GreaterThanThreshold"
     evaluation_periods  = "2"
     metric_name         = "CPUUtilization"
     namespace           = "AWS/RDS"
     period              = "300"
     statistic           = "Average"
     threshold           = "80"
     alarm_description   = "This metric monitors database CPU utilization"
     alarm_actions       = [var.sns_topic_arn]
   
     dimensions = {
       DBInstanceIdentifier = var.db_instance_id
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-database-cpu-alarm"
       Environment = var.environment
     }
   }
   
   # Database Connection Count Alarm
   resource "aws_cloudwatch_metric_alarm" "database_connections" {
     alarm_name          = "${var.project_name}-${var.environment}-database-connections"
     comparison_operator = "GreaterThanThreshold"
     evaluation_periods  = "2"
     metric_name         = "DatabaseConnections"
     namespace           = "AWS/RDS"
     period              = "300"
     statistic           = "Average"
     threshold           = "15"
     alarm_description   = "This metric monitors database connection count"
     alarm_actions       = [var.sns_topic_arn]
   
     dimensions = {
       DBInstanceIdentifier = var.db_instance_id
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-database-connections-alarm"
       Environment = var.environment
     }
   }
   
   # Database Free Storage Space Alarm
   resource "aws_cloudwatch_metric_alarm" "database_free_storage" {
     alarm_name          = "${var.project_name}-${var.environment}-database-storage"
     comparison_operator = "LessThanThreshold"
     evaluation_periods  = "2"
     metric_name         = "FreeStorageSpace"
     namespace           = "AWS/RDS"
     period              = "300"
     statistic           = "Average"
     threshold           = "2000000000"  # 2GB in bytes
     alarm_description   = "This metric monitors database free storage"
     alarm_actions       = [var.sns_topic_arn]
   
     dimensions = {
       DBInstanceIdentifier = var.db_instance_id
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-database-storage-alarm"
       Environment = var.environment
     }
   }
   ```

### Task 2: Create SNS Topic for Alerts

1. **Create `terraform/modules/monitoring/sns.tf`:**
   ```hcl
   # SNS Topic for Database Alerts
   resource "aws_sns_topic" "database_alerts" {
     name = "${var.project_name}-${var.environment}-database-alerts"
   
     tags = {
       Name = "${var.project_name}-${var.environment}-database-alerts"
       Environment = var.environment
     }
   }
   
   # SNS Topic Subscription
   resource "aws_sns_topic_subscription" "database_alerts_email" {
     count     = length(var.alert_email_addresses)
     topic_arn = aws_sns_topic.database_alerts.arn
     protocol  = "email"
     endpoint  = var.alert_email_addresses[count.index]
   }
   ```

### ✅ Verification

1. **Check monitoring configuration:**
   ```bash
   terraform plan -target=module.monitoring
   ```

2. **Validate alarm thresholds:**
   ```bash
   aws cloudwatch describe-alarms --alarm-names "${PROJECT_NAME}-${ENVIRONMENT}-database-cpu"
   ```

---

## Exercise 4: Deploy and Test Database Connectivity

### Task 1: Update Environment Configuration

1. **Create `terraform/environments/dev/database.tf`:**
   ```hcl
   # Database secrets
   module "secrets" {
     source = "../../modules/secrets"
   
     project_name      = var.project_name
     environment       = var.environment
     database_username = "taskuser"
   }
   
   # Database instance
   module "database" {
     source = "../../modules/rds"
   
     project_name      = var.project_name
     environment       = var.environment
     database_subnets  = module.vpc.database_subnet_ids
     security_group_ids = [module.security_groups.database_security_group_id]
   
     instance_class    = "db.t3.micro"
     allocated_storage = 20
     database_name     = "taskmanager"
     database_username = "taskuser"
     database_password = module.secrets.db_password
   
     backup_retention_period = 7
     deletion_protection     = false  # Set to true for production
     skip_final_snapshot    = true   # Set to false for production
   }
   
   # Database monitoring
   module "database_monitoring" {
     source = "../../modules/monitoring"
   
     project_name    = var.project_name
     environment     = var.environment
     db_instance_id  = module.database.db_instance_id
     sns_topic_arn   = aws_sns_topic.database_alerts.arn
   }
   ```

2. **Update `terraform/environments/dev/main.tf`:**
   ```hcl
   # VPC Configuration
   module "vpc" {
     source = "../../modules/vpc"
   
     project_name = var.project_name
     environment  = var.environment
     vpc_cidr     = "10.0.0.0/16"
   
     public_subnet_cidrs   = ["10.0.1.0/24", "10.0.2.0/24"]
     private_subnet_cidrs  = ["10.0.3.0/24", "10.0.4.0/24"]
     database_subnet_cidrs = ["10.0.5.0/24", "10.0.6.0/24"]
   
     availability_zones = ["us-east-1a", "us-east-1b"]
   }
   ```

### Task 2: Deploy Database Infrastructure

1. **Initialize and plan:**
   ```bash
   cd terraform/environments/dev
   terraform init
   terraform plan
   ```

2. **Deploy database infrastructure:**
   ```bash
   terraform apply
   ```

3. **Get database endpoint:**
   ```bash
   terraform output db_endpoint
   ```

### Task 3: Test Database Connectivity

1. **Connect to database from EC2 instance:**
   ```bash
   # Get database endpoint
   DB_ENDPOINT=$(terraform output -raw db_endpoint)
   
   # Test connection (you'll need to create a test EC2 instance first)
   psql -h $DB_ENDPOINT -U taskuser -d taskmanager
   ```

2. **Test from application container:**
   ```bash
   # Update docker-compose.yml with RDS endpoint
   docker-compose exec web python -c "
   import psycopg2
   try:
       conn = psycopg2.connect(
           host='$DB_ENDPOINT',
           database='taskmanager',
           user='taskuser',
           password='$DB_PASSWORD'
       )
       print('Database connection successful!')
       conn.close()
   except Exception as e:
       print(f'Connection failed: {e}')
   "
   ```

### ✅ Verification

1. **Check RDS instance status:**
   ```bash
   aws rds describe-db-instances --db-instance-identifier "${PROJECT_NAME}-${ENVIRONMENT}-db"
   ```

2. **Verify monitoring alarms:**
   ```bash
   aws cloudwatch describe-alarms --alarm-name-prefix "${PROJECT_NAME}-${ENVIRONMENT}-database"
   ```

3. **Test database performance:**
   ```bash
   aws rds describe-db-instances --db-instance-identifier "${PROJECT_NAME}-${ENVIRONMENT}-db" \
     --query 'DBInstances[0].PerformanceInsightsEnabled'
   ```

---

## Exercise 5: Create Database Initialization Scripts

### Task 1: Create Database Schema Script

1. **Create `scripts/db-init.sql`:**
   ```sql
   -- Create database schema
   CREATE SCHEMA IF NOT EXISTS taskmanager;
   
   -- Create users table
   CREATE TABLE IF NOT EXISTS users (
       id SERIAL PRIMARY KEY,
       username VARCHAR(80) UNIQUE NOT NULL,
       email VARCHAR(120) UNIQUE NOT NULL,
       password_hash VARCHAR(255) NOT NULL,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   
   -- Create task status enum
   CREATE TYPE task_status AS ENUM ('pending', 'in_progress', 'completed');
   
   -- Create task priority enum
   CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high');
   
   -- Create tasks table
   CREATE TABLE IF NOT EXISTS tasks (
       id SERIAL PRIMARY KEY,
       title VARCHAR(200) NOT NULL,
       description TEXT,
       status task_status DEFAULT 'pending',
       priority task_priority DEFAULT 'medium',
       user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
       due_date DATE,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   
   -- Create indexes
   CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
   CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
   CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
   CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
   
   -- Create updated_at trigger function
   CREATE OR REPLACE FUNCTION update_updated_at_column()
   RETURNS TRIGGER AS $$
   BEGIN
       NEW.updated_at = CURRENT_TIMESTAMP;
       RETURN NEW;
   END;
   $$ language 'plpgsql';
   
   -- Create triggers
   CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
   FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
   
   CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
   FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
   ```

2. **Create `scripts/db-seed.sql`:**
   ```sql
   -- Insert sample users
   INSERT INTO users (username, email, password_hash) VALUES
   ('john_doe', 'john@example.com', 'pbkdf2:sha256:260000$...'),
   ('jane_smith', 'jane@example.com', 'pbkdf2:sha256:260000$...'),
   ('mike_wilson', 'mike@example.com', 'pbkdf2:sha256:260000$...')
   ON CONFLICT (username) DO NOTHING;
   
   -- Insert sample tasks
   INSERT INTO tasks (title, description, status, priority, user_id, due_date) VALUES
   ('Complete project proposal', 'Draft and submit the Q1 project proposal', 'pending', 'high', 1, '2024-02-15'),
   ('Review code changes', 'Review pull request #123', 'in_progress', 'medium', 1, '2024-02-10'),
   ('Update documentation', 'Update API documentation', 'completed', 'low', 2, '2024-02-08'),
   ('Fix database migration', 'Resolve schema migration issue', 'pending', 'high', 2, '2024-02-12'),
   ('Team meeting preparation', 'Prepare slides for weekly team meeting', 'in_progress', 'medium', 3, '2024-02-09'),
   ('Security audit', 'Conduct security review of authentication system', 'pending', 'high', 3, '2024-02-20'),
   ('Performance optimization', 'Optimize database queries', 'completed', 'medium', 1, '2024-02-05'),
   ('User feedback analysis', 'Analyze user feedback from last release', 'pending', 'low', 2, '2024-02-25')
   ON CONFLICT DO NOTHING;
   ```

### Task 2: Create Database Migration Tool

1. **Create `scripts/db-migrate.py`:**
   ```python
   #!/usr/bin/env python3
   import os
   import sys
   import psycopg2
   import argparse
   from datetime import datetime
   
   def get_db_connection():
       """Get database connection from environment variables"""
       return psycopg2.connect(
           host=os.getenv('DB_HOST'),
           database=os.getenv('DB_NAME'),
           user=os.getenv('DB_USER'),
           password=os.getenv('DB_PASSWORD'),
           port=os.getenv('DB_PORT', '5432')
       )
   
   def run_sql_file(cursor, file_path):
       """Execute SQL file"""
       with open(file_path, 'r') as file:
           cursor.execute(file.read())
       print(f"Successfully executed: {file_path}")
   
   def main():
       parser = argparse.ArgumentParser(description='Database migration tool')
       parser.add_argument('--init', action='store_true', help='Initialize database schema')
       parser.add_argument('--seed', action='store_true', help='Seed database with sample data')
       parser.add_argument('--reset', action='store_true', help='Reset database (drop and recreate)')
       
       args = parser.parse_args()
       
       try:
           conn = get_db_connection()
           cursor = conn.cursor()
           
           if args.reset:
               print("Resetting database...")
               cursor.execute("DROP SCHEMA IF EXISTS taskmanager CASCADE;")
               cursor.execute("DROP TYPE IF EXISTS task_status CASCADE;")
               cursor.execute("DROP TYPE IF EXISTS task_priority CASCADE;")
               conn.commit()
               print("Database reset completed")
           
           if args.init or args.reset:
               print("Initializing database schema...")
               run_sql_file(cursor, 'db-init.sql')
               conn.commit()
               print("Database schema initialized")
           
           if args.seed:
               print("Seeding database with sample data...")
               run_sql_file(cursor, 'db-seed.sql')
               conn.commit()
               print("Database seeded successfully")
           
       except Exception as e:
           print(f"Error: {e}")
           sys.exit(1)
       finally:
           if 'conn' in locals():
               conn.close()
   
   if __name__ == '__main__':
       main()
   ```

2. **Make script executable:**
   ```bash
   chmod +x scripts/db-migrate.py
   ```

### Task 3: Create Database Backup Script

1. **Create `scripts/db-backup.sh`:**
   ```bash
   #!/bin/bash
   
   # Database backup script
   
   set -e
   
   # Configuration
   BACKUP_DIR="/backups"
   TIMESTAMP=$(date +%Y%m%d_%H%M%S)
   BACKUP_FILE="taskmanager_backup_${TIMESTAMP}.sql"
   
   # Create backup directory
   mkdir -p $BACKUP_DIR
   
   # Create database backup
   pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > $BACKUP_DIR/$BACKUP_FILE
   
   # Compress backup
   gzip $BACKUP_DIR/$BACKUP_FILE
   
   # Upload to S3 (optional)
   if [ ! -z "$AWS_S3_BUCKET" ]; then
       aws s3 cp $BACKUP_DIR/$BACKUP_FILE.gz s3://$AWS_S3_BUCKET/backups/
   fi
   
   # Clean up old backups (keep last 7 days)
   find $BACKUP_DIR -name "taskmanager_backup_*.sql.gz" -mtime +7 -delete
   
   echo "Backup completed: $BACKUP_FILE.gz"
   ```

2. **Make script executable:**
   ```bash
   chmod +x scripts/db-backup.sh
   ```

### ✅ Verification

1. **Test database initialization:**
   ```bash
   export DB_HOST=$(terraform output -raw db_endpoint)
   export DB_NAME="taskmanager"
   export DB_USER="taskuser"
   export DB_PASSWORD=$(terraform output -raw db_password)
   
   python scripts/db-migrate.py --init
   ```

2. **Test database seeding:**
   ```bash
   python scripts/db-migrate.py --seed
   ```

3. **Verify data:**
   ```bash
   psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM users;"
   psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM tasks;"
   ```

---

## Summary

In this lab, you have successfully:

✅ **Created secure RDS PostgreSQL infrastructure:**
- Implemented RDS Terraform module with security best practices
- Configured database subnet groups and parameter groups
- Set up proper encryption and access controls

✅ **Implemented database security and networking:**
- Created dedicated security groups for database access
- Configured secrets management with AWS Secrets Manager
- Set up private database subnets with proper routing

✅ **Set up backup and monitoring:**
- Created CloudWatch alarms for database metrics
- Implemented automated backup configuration
- Set up SNS notifications for database alerts

✅ **Deployed and tested database connectivity:**
- Successfully deployed RDS instance to AWS
- Verified database connectivity from application
- Tested performance insights and monitoring

✅ **Created database management tools:**
- Built database initialization and migration scripts
- Created database seeding tools with sample data
- Implemented backup and maintenance scripts

## Next Steps

Your database infrastructure is now secure and ready for production use. In the next lab, you will:

- Create Application Load Balancer for high availability
- Set up EC2 instances with auto-scaling groups
- Configure health checks and monitoring
- Implement blue-green deployment strategies

## Troubleshooting

### Common Issues

**Issue:** Database connection timeout
**Solution:**
- Check security group rules allow connections from web servers
- Verify database is in correct subnet group
- Ensure VPC routing is configured properly

**Issue:** Database performance issues
**Solution:**
- Review CloudWatch metrics for CPU and memory usage
- Check database parameter group settings
- Consider upgrading instance class if needed

**Issue:** Backup failures
**Solution:**
- Verify backup window doesn't conflict with maintenance window
- Check IAM permissions for backup operations
- Ensure sufficient storage space for backups

### Additional Resources

- [AWS RDS Documentation](https://docs.aws.amazon.com/rds/)
- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/performance-tips.html)
- [AWS RDS Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html)

---

**🎉 Congratulations!** You have successfully completed Lab 03. Your database infrastructure is now secure, scalable, and ready for production workloads.

**Next:** [Lab 04: Compute Infrastructure and Load Balancing](./04-compute-infrastructure-load-balancing.md)