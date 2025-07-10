# Lab 04: Compute Infrastructure and Load Balancing

## Overview

In this lab, you will create a scalable compute infrastructure using AWS EC2 instances, Application Load Balancer (ALB), and Auto Scaling Groups. You'll implement health checks, configure load balancing, and set up automated scaling policies to handle varying traffic loads.

## Objectives

After completing this lab, you will be able to:
- Create Application Load Balancer with proper health checks
- Design EC2 launch templates with user data scripts
- Implement Auto Scaling Groups with scaling policies
- Configure load balancer target groups and routing
- Set up monitoring and alerting for compute resources

## Prerequisites

- Completed Lab 03 (Database Infrastructure and Management)
- Understanding of AWS compute services
- Basic knowledge of load balancing concepts
- Existing VPC and database infrastructure

## Duration

**Estimated Time:** 75 minutes

---

## Exercise 1: Create Application Load Balancer Configuration

### Task 1: Create ALB Terraform Module

1. **Create ALB module directory:**
   ```bash
   mkdir -p terraform/modules/alb
   cd terraform/modules/alb
   ```

2. **Create `main.tf` for ALB resources:**
   ```hcl
   # Application Load Balancer
   resource "aws_lb" "main" {
     name               = "${var.project_name}-${var.environment}-alb"
     internal           = false
     load_balancer_type = "application"
     security_groups    = var.security_group_ids
     subnets            = var.public_subnet_ids
   
     enable_deletion_protection = var.enable_deletion_protection
   
     access_logs {
       bucket  = aws_s3_bucket.alb_logs.bucket
       prefix  = "alb-logs"
       enabled = true
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-alb"
       Environment = var.environment
     }
   }
   
   # S3 Bucket for ALB Access Logs
   resource "aws_s3_bucket" "alb_logs" {
     bucket = "${var.project_name}-${var.environment}-alb-logs-${random_id.bucket_suffix.hex}"
   
     tags = {
       Name = "${var.project_name}-${var.environment}-alb-logs"
       Environment = var.environment
     }
   }
   
   resource "random_id" "bucket_suffix" {
     byte_length = 8
   }
   
   resource "aws_s3_bucket_policy" "alb_logs" {
     bucket = aws_s3_bucket.alb_logs.id
   
     policy = jsonencode({
       Version = "2012-10-17"
       Statement = [
         {
           Effect = "Allow"
           Principal = {
             AWS = "arn:aws:iam::${data.aws_elb_service_account.main.id}:root"
           }
           Action   = "s3:PutObject"
           Resource = "${aws_s3_bucket.alb_logs.arn}/*"
         },
         {
           Effect = "Allow"
           Principal = {
             Service = "delivery.logs.amazonaws.com"
           }
           Action   = "s3:PutObject"
           Resource = "${aws_s3_bucket.alb_logs.arn}/*"
         }
       ]
     })
   }
   
   data "aws_elb_service_account" "main" {}
   
   # Target Group for Web Application
   resource "aws_lb_target_group" "web" {
     name     = "${var.project_name}-${var.environment}-web-tg"
     port     = 5000
     protocol = "HTTP"
     vpc_id   = var.vpc_id
   
     health_check {
       enabled             = true
       healthy_threshold   = 2
       unhealthy_threshold = 2
       timeout             = 5
       interval            = 30
       path                = "/health"
       matcher             = "200"
       port                = "traffic-port"
       protocol            = "HTTP"
     }
   
     stickiness {
       type            = "lb_cookie"
       cookie_duration = 86400
       enabled         = true
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-web-tg"
       Environment = var.environment
     }
   }
   
   # ALB Listener for HTTP traffic
   resource "aws_lb_listener" "web" {
     load_balancer_arn = aws_lb.main.arn
     port              = "80"
     protocol          = "HTTP"
   
     default_action {
       type             = "forward"
       target_group_arn = aws_lb_target_group.web.arn
     }
   }
   
   # ALB Listener for HTTPS traffic (optional)
   resource "aws_lb_listener" "web_https" {
     count = var.certificate_arn != "" ? 1 : 0
     
     load_balancer_arn = aws_lb.main.arn
     port              = "443"
     protocol          = "HTTPS"
     ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
     certificate_arn   = var.certificate_arn
   
     default_action {
       type             = "forward"
       target_group_arn = aws_lb_target_group.web.arn
     }
   }
   
   # Redirect HTTP to HTTPS (if certificate is provided)
   resource "aws_lb_listener_rule" "redirect_http_to_https" {
     count = var.certificate_arn != "" ? 1 : 0
     
     listener_arn = aws_lb_listener.web.arn
     priority     = 100
   
     action {
       type = "redirect"
   
       redirect {
         port        = "443"
         protocol    = "HTTPS"
         status_code = "HTTP_301"
       }
     }
   
     condition {
       path_pattern {
         values = ["*"]
       }
     }
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
   
   variable "vpc_id" {
     description = "VPC ID"
     type        = string
   }
   
   variable "public_subnet_ids" {
     description = "List of public subnet IDs"
     type        = list(string)
   }
   
   variable "security_group_ids" {
     description = "List of security group IDs"
     type        = list(string)
   }
   
   variable "enable_deletion_protection" {
     description = "Enable deletion protection for ALB"
     type        = bool
     default     = false
   }
   
   variable "certificate_arn" {
     description = "ARN of SSL certificate for HTTPS"
     type        = string
     default     = ""
   }
   ```

4. **Create `outputs.tf`:**
   ```hcl
   output "alb_arn" {
     description = "ARN of the Application Load Balancer"
     value       = aws_lb.main.arn
   }
   
   output "alb_dns_name" {
     description = "DNS name of the Application Load Balancer"
     value       = aws_lb.main.dns_name
   }
   
   output "alb_zone_id" {
     description = "Zone ID of the Application Load Balancer"
     value       = aws_lb.main.zone_id
   }
   
   output "target_group_arn" {
     description = "ARN of the target group"
     value       = aws_lb_target_group.web.arn
   }
   
   output "alb_security_group_id" {
     description = "Security group ID of the ALB"
     value       = var.security_group_ids[0]
   }
   ```

### Task 2: Update Security Groups for ALB

1. **Update `terraform/modules/security-groups/main.tf`:**
   ```hcl
   # ALB Security Group
   resource "aws_security_group" "alb" {
     name        = "${var.project_name}-${var.environment}-alb-sg"
     description = "Security group for Application Load Balancer"
     vpc_id      = var.vpc_id
   
     ingress {
       from_port   = 80
       to_port     = 80
       protocol    = "tcp"
       cidr_blocks = ["0.0.0.0/0"]
       description = "HTTP from anywhere"
     }
   
     ingress {
       from_port   = 443
       to_port     = 443
       protocol    = "tcp"
       cidr_blocks = ["0.0.0.0/0"]
       description = "HTTPS from anywhere"
     }
   
     egress {
       from_port   = 0
       to_port     = 0
       protocol    = "-1"
       cidr_blocks = ["0.0.0.0/0"]
       description = "All outbound traffic"
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-alb-sg"
       Environment = var.environment
     }
   }
   
   # Update Web Security Group to allow ALB traffic
   resource "aws_security_group_rule" "web_from_alb" {
     type                     = "ingress"
     from_port                = 5000
     to_port                  = 5000
     protocol                 = "tcp"
     source_security_group_id = aws_security_group.alb.id
     security_group_id        = aws_security_group.web.id
     description              = "Allow ALB to reach web servers"
   }
   ```

2. **Add ALB security group output:**
   ```hcl
   output "alb_security_group_id" {
     description = "ID of the ALB security group"
     value       = aws_security_group.alb.id
   }
   ```

### ✅ Verification

1. **Validate ALB module:**
   ```bash
   cd terraform/modules/alb
   terraform validate
   ```

2. **Check security group rules:**
   ```bash
   terraform plan -target=module.security_groups
   ```

---

## Exercise 2: Design EC2 Launch Templates and Auto Scaling

### Task 1: Create EC2 Launch Template

1. **Create `terraform/modules/ec2/main.tf`:**
   ```hcl
   # IAM Role for EC2 instances
   resource "aws_iam_role" "ec2_role" {
     name = "${var.project_name}-${var.environment}-ec2-role"
   
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
   
     tags = {
       Name = "${var.project_name}-${var.environment}-ec2-role"
       Environment = var.environment
     }
   }
   
   # IAM Policy for EC2 instances
   resource "aws_iam_role_policy" "ec2_policy" {
     name = "${var.project_name}-${var.environment}-ec2-policy"
     role = aws_iam_role.ec2_role.id
   
     policy = jsonencode({
       Version = "2012-10-17"
       Statement = [
         {
           Effect = "Allow"
           Action = [
             "secretsmanager:GetSecretValue",
             "secretsmanager:DescribeSecret",
             "logs:CreateLogGroup",
             "logs:CreateLogStream",
             "logs:PutLogEvents",
             "logs:DescribeLogStreams",
             "cloudwatch:PutMetricData",
             "ec2:DescribeVolumes",
             "ec2:DescribeTags",
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
   
   # Instance Profile
   resource "aws_iam_instance_profile" "ec2_profile" {
     name = "${var.project_name}-${var.environment}-ec2-profile"
     role = aws_iam_role.ec2_role.name
   }
   
   # Launch Template
   resource "aws_launch_template" "web" {
     name_prefix   = "${var.project_name}-${var.environment}-web-"
     image_id      = var.ami_id
     instance_type = var.instance_type
     key_name      = var.key_name
   
     vpc_security_group_ids = var.security_group_ids
   
     iam_instance_profile {
       name = aws_iam_instance_profile.ec2_profile.name
     }
   
     user_data = base64encode(templatefile("${path.module}/user_data.sh", {
       project_name = var.project_name
       environment  = var.environment
       db_secret_arn = var.db_secret_arn
       ecr_repository_url = var.ecr_repository_url
     }))
   
     tag_specifications {
       resource_type = "instance"
       tags = {
         Name = "${var.project_name}-${var.environment}-web"
         Environment = var.environment
       }
     }
   
     tag_specifications {
       resource_type = "volume"
       tags = {
         Name = "${var.project_name}-${var.environment}-web-volume"
         Environment = var.environment
       }
     }
   
     lifecycle {
       create_before_destroy = true
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-web-template"
       Environment = var.environment
     }
   }
   
   # Auto Scaling Group
   resource "aws_autoscaling_group" "web" {
     name                = "${var.project_name}-${var.environment}-web-asg"
     vpc_zone_identifier = var.private_subnet_ids
     target_group_arns   = [var.target_group_arn]
     health_check_type   = "ELB"
     health_check_grace_period = 300
   
     min_size         = var.min_size
     max_size         = var.max_size
     desired_capacity = var.desired_capacity
   
     launch_template {
       id      = aws_launch_template.web.id
       version = "$Latest"
     }
   
     instance_refresh {
       strategy = "Rolling"
       preferences {
         min_healthy_percentage = 50
       }
       triggers = ["tag"]
     }
   
     tag {
       key                 = "Name"
       value               = "${var.project_name}-${var.environment}-web-asg"
       propagate_at_launch = false
     }
   
     tag {
       key                 = "Environment"
       value               = var.environment
       propagate_at_launch = true
     }
   
     lifecycle {
       create_before_destroy = true
     }
   }
   
   # Auto Scaling Policies
   resource "aws_autoscaling_policy" "scale_up" {
     name                   = "${var.project_name}-${var.environment}-scale-up"
     scaling_adjustment     = 1
     adjustment_type        = "ChangeInCapacity"
     cooldown              = 300
     autoscaling_group_name = aws_autoscaling_group.web.name
   }
   
   resource "aws_autoscaling_policy" "scale_down" {
     name                   = "${var.project_name}-${var.environment}-scale-down"
     scaling_adjustment     = -1
     adjustment_type        = "ChangeInCapacity"
     cooldown              = 300
     autoscaling_group_name = aws_autoscaling_group.web.name
   }
   
   # CloudWatch Alarms for Auto Scaling
   resource "aws_cloudwatch_metric_alarm" "cpu_high" {
     alarm_name          = "${var.project_name}-${var.environment}-cpu-high"
     comparison_operator = "GreaterThanThreshold"
     evaluation_periods  = "2"
     metric_name         = "CPUUtilization"
     namespace           = "AWS/EC2"
     period              = "300"
     statistic           = "Average"
     threshold           = "80"
     alarm_description   = "This metric monitors ec2 cpu utilization"
     alarm_actions       = [aws_autoscaling_policy.scale_up.arn]
   
     dimensions = {
       AutoScalingGroupName = aws_autoscaling_group.web.name
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-cpu-high-alarm"
       Environment = var.environment
     }
   }
   
   resource "aws_cloudwatch_metric_alarm" "cpu_low" {
     alarm_name          = "${var.project_name}-${var.environment}-cpu-low"
     comparison_operator = "LessThanThreshold"
     evaluation_periods  = "2"
     metric_name         = "CPUUtilization"
     namespace           = "AWS/EC2"
     period              = "300"
     statistic           = "Average"
     threshold           = "20"
     alarm_description   = "This metric monitors ec2 cpu utilization"
     alarm_actions       = [aws_autoscaling_policy.scale_down.arn]
   
     dimensions = {
       AutoScalingGroupName = aws_autoscaling_group.web.name
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-cpu-low-alarm"
       Environment = var.environment
     }
   }
   ```

2. **Create `terraform/modules/ec2/user_data.sh`:**
   ```bash
   #!/bin/bash
   yum update -y
   yum install -y docker aws-cli jq
   
   # Start Docker service
   service docker start
   usermod -a -G docker ec2-user
   
   # Install Docker Compose
   curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   chmod +x /usr/local/bin/docker-compose
   
   # Create application directory
   mkdir -p /opt/app
   cd /opt/app
   
   # Get database credentials from Secrets Manager
   DB_SECRET=$(aws secretsmanager get-secret-value --secret-id "${db_secret_arn}" --region us-east-1 --query SecretString --output text)
   DB_PASSWORD=$(echo $DB_SECRET | jq -r '.password')
   DB_USERNAME=$(echo $DB_SECRET | jq -r '.username')
   
   # Create environment file
   cat > .env << EOF
   FLASK_ENV=production
   FLASK_DEBUG=false
   DATABASE_URL=postgresql://$DB_USERNAME:$DB_PASSWORD@${db_endpoint}:5432/taskmanager
   SECRET_KEY=$(openssl rand -base64 32)
   EOF
   
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${ecr_repository_url}
   
   # Pull and run the application
   docker pull ${ecr_repository_url}:latest
   docker run -d \
     --name taskmanager \
     --restart unless-stopped \
     -p 5000:5000 \
     --env-file .env \
     ${ecr_repository_url}:latest
   
   # Install CloudWatch agent
   wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
   rpm -U ./amazon-cloudwatch-agent.rpm
   
   # Configure CloudWatch agent
   cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << EOF
   {
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
     },
     "logs": {
       "logs_collected": {
         "files": {
           "collect_list": [
             {
               "file_path": "/var/log/messages",
               "log_group_name": "/aws/ec2/${project_name}-${environment}",
               "log_stream_name": "{instance_id}/system"
             }
           ]
         }
       }
     }
   }
   EOF
   
   # Start CloudWatch agent
   /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s
   
   # Create health check script
   cat > /opt/app/health_check.sh << 'EOF'
   #!/bin/bash
   response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health)
   if [ $response -eq 200 ]; then
     exit 0
   else
     exit 1
   fi
   EOF
   
   chmod +x /opt/app/health_check.sh
   
   # Add health check to cron
   echo "*/1 * * * * /opt/app/health_check.sh || docker restart taskmanager" | crontab -
   ```

3. **Create `terraform/modules/ec2/variables.tf`:**
   ```hcl
   variable "project_name" {
     description = "Name of the project"
     type        = string
   }
   
   variable "environment" {
     description = "Environment name"
     type        = string
   }
   
   variable "vpc_id" {
     description = "VPC ID"
     type        = string
   }
   
   variable "private_subnet_ids" {
     description = "List of private subnet IDs"
     type        = list(string)
   }
   
   variable "security_group_ids" {
     description = "List of security group IDs"
     type        = list(string)
   }
   
   variable "target_group_arn" {
     description = "ARN of the target group"
     type        = string
   }
   
   variable "ami_id" {
     description = "AMI ID for EC2 instances"
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
     default     = 2
   }
   
   variable "db_secret_arn" {
     description = "ARN of the database secret"
     type        = string
   }
   
   variable "ecr_repository_url" {
     description = "ECR repository URL"
     type        = string
   }
   ```

4. **Create `terraform/modules/ec2/outputs.tf`:**
   ```hcl
   output "autoscaling_group_name" {
     description = "Name of the Auto Scaling Group"
     value       = aws_autoscaling_group.web.name
   }
   
   output "autoscaling_group_arn" {
     description = "ARN of the Auto Scaling Group"
     value       = aws_autoscaling_group.web.arn
   }
   
   output "launch_template_id" {
     description = "ID of the launch template"
     value       = aws_launch_template.web.id
   }
   
   output "iam_role_name" {
     description = "Name of the IAM role for EC2 instances"
     value       = aws_iam_role.ec2_role.name
   }
   ```

### ✅ Verification

1. **Validate EC2 module:**
   ```bash
   cd terraform/modules/ec2
   terraform validate
   ```

2. **Check user data script:**
   ```bash
   bash -n user_data.sh
   ```

---

## Exercise 3: Implement Health Checks and Monitoring

### Task 1: Create ECR Repository

1. **Create `terraform/modules/ecr/main.tf`:**
   ```hcl
   # ECR Repository
   resource "aws_ecr_repository" "main" {
     name                 = "${var.project_name}-${var.environment}"
     image_tag_mutability = "MUTABLE"
   
     image_scanning_configuration {
       scan_on_push = true
     }
   
     encryption_configuration {
       encryption_type = "AES256"
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}"
       Environment = var.environment
     }
   }
   
   # ECR Lifecycle Policy
   resource "aws_ecr_lifecycle_policy" "main" {
     repository = aws_ecr_repository.main.name
   
     policy = jsonencode({
       rules = [
         {
           rulePriority = 1
           description  = "Keep last 10 images"
           selection = {
             tagStatus     = "tagged"
             tagPrefixList = ["v"]
             countType     = "imageCountMoreThan"
             countNumber   = 10
           }
           action = {
             type = "expire"
           }
         },
         {
           rulePriority = 2
           description  = "Delete untagged images older than 1 day"
           selection = {
             tagStatus   = "untagged"
             countType   = "sinceImagePushed"
             countUnit   = "days"
             countNumber = 1
           }
           action = {
             type = "expire"
           }
         }
       ]
     })
   }
   ```

2. **Create `terraform/modules/ecr/variables.tf`:**
   ```hcl
   variable "project_name" {
     description = "Name of the project"
     type        = string
   }
   
   variable "environment" {
     description = "Environment name"
     type        = string
   }
   ```

3. **Create `terraform/modules/ecr/outputs.tf`:**
   ```hcl
   output "repository_url" {
     description = "ECR repository URL"
     value       = aws_ecr_repository.main.repository_url
   }
   
   output "repository_name" {
     description = "ECR repository name"
     value       = aws_ecr_repository.main.name
   }
   ```

### Task 2: Create CloudWatch Dashboard

1. **Create `terraform/modules/monitoring/dashboard.tf`:**
   ```hcl
   # CloudWatch Dashboard
   resource "aws_cloudwatch_dashboard" "main" {
     dashboard_name = "${var.project_name}-${var.environment}-dashboard"
   
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
               ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", var.alb_name],
               [".", "RequestCount", ".", "."],
               [".", "HTTPCode_Target_2XX_Count", ".", "."],
               [".", "HTTPCode_Target_4XX_Count", ".", "."],
               [".", "HTTPCode_Target_5XX_Count", ".", "."]
             ]
             period = 300
             stat   = "Average"
             region = "us-east-1"
             title  = "ALB Metrics"
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
               ["AWS/EC2", "CPUUtilization", "AutoScalingGroupName", var.asg_name],
               [".", "NetworkIn", ".", "."],
               [".", "NetworkOut", ".", "."]
             ]
             period = 300
             stat   = "Average"
             region = "us-east-1"
             title  = "EC2 Metrics"
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
               ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", var.db_instance_id],
               [".", "DatabaseConnections", ".", "."],
               [".", "ReadLatency", ".", "."],
               [".", "WriteLatency", ".", "."]
             ]
             period = 300
             stat   = "Average"
             region = "us-east-1"
             title  = "RDS Metrics"
             yAxis = {
               left = {
                 min = 0
               }
             }
           }
         }
       ]
     })
   }
   ```

### ✅ Verification

1. **Validate monitoring module:**
   ```bash
   cd terraform/modules/monitoring
   terraform validate
   ```

2. **Check dashboard configuration:**
   ```bash
   terraform plan -target=aws_cloudwatch_dashboard.main
   ```

---

## Exercise 4: Deploy and Configure Load Balancer

### Task 1: Update Environment Configuration

1. **Create `terraform/environments/dev/compute.tf`:**
   ```hcl
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
   
     enable_deletion_protection = false
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
     instance_type       = "t3.micro"
     key_name            = var.key_name
     min_size            = 1
     max_size            = 3
     desired_capacity    = 2
   
     db_secret_arn       = module.secrets.db_secret_arn
     ecr_repository_url  = module.ecr.repository_url
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

2. **Update `terraform/environments/dev/variables.tf`:**
   ```hcl
   variable "key_name" {
     description = "EC2 Key Pair name"
     type        = string
   }
   ```

### Task 2: Deploy Compute Infrastructure

1. **Create EC2 Key Pair:**
   ```bash
   aws ec2 create-key-pair \
     --key-name taskmanager-dev \
     --query 'KeyMaterial' \
     --output text > taskmanager-dev.pem
   
   chmod 400 taskmanager-dev.pem
   ```

2. **Deploy infrastructure:**
   ```bash
   cd terraform/environments/dev
   terraform init
   terraform plan -var="key_name=taskmanager-dev"
   terraform apply -var="key_name=taskmanager-dev"
   ```

3. **Get ALB DNS name:**
   ```bash
   ALB_DNS=$(terraform output -raw alb_dns_name)
   echo "Application URL: http://$ALB_DNS"
   ```

### Task 3: Build and Push Docker Image

1. **Build Docker image:**
   ```bash
   cd ../../../
   docker build -t taskmanager:latest .
   ```

2. **Tag image for ECR:**
   ```bash
   ECR_URL=$(cd terraform/environments/dev && terraform output -raw ecr_repository_url)
   docker tag taskmanager:latest $ECR_URL:latest
   ```

3. **Push to ECR:**
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URL
   docker push $ECR_URL:latest
   ```

### ✅ Verification

1. **Check ALB health:**
   ```bash
   ALB_DNS=$(cd terraform/environments/dev && terraform output -raw alb_dns_name)
   curl -I http://$ALB_DNS/health
   ```

2. **Check Auto Scaling Group:**
   ```bash
   ASG_NAME=$(cd terraform/environments/dev && terraform output -raw asg_name)
   aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names $ASG_NAME
   ```

3. **Check target group health:**
   ```bash
   TG_ARN=$(cd terraform/environments/dev && terraform output -raw target_group_arn)
   aws elbv2 describe-target-health --target-group-arn $TG_ARN
   ```

---

## Exercise 5: Test Load Balancing and Scaling Behavior

### Task 1: Test Load Balancer Functionality

1. **Test application through ALB:**
   ```bash
   ALB_DNS=$(cd terraform/environments/dev && terraform output -raw alb_dns_name)
   
   # Test health endpoint
   curl http://$ALB_DNS/health
   
   # Test main application
   curl http://$ALB_DNS/
   
   # Test API endpoints
   curl http://$ALB_DNS/api/users
   curl http://$ALB_DNS/api/tasks
   ```

2. **Test load balancing:**
   ```bash
   # Make multiple requests to see load balancing
   for i in {1..10}; do
     curl -s http://$ALB_DNS/api/dashboard-stats | jq '.timestamp'
     sleep 1
   done
   ```

3. **Test session stickiness:**
   ```bash
   # Test with cookies
   curl -c cookies.txt http://$ALB_DNS/
   curl -b cookies.txt http://$ALB_DNS/api/dashboard-stats
   ```

### Task 2: Test Auto Scaling

1. **Generate load to trigger scaling:**
   ```bash
   # Install stress testing tool
   sudo yum install -y stress
   
   # Connect to EC2 instance
   INSTANCE_ID=$(aws ec2 describe-instances \
     --filters "Name=tag:Name,Values=taskmanager-dev-web" \
     --query 'Reservations[0].Instances[0].InstanceId' \
     --output text)
   
   aws ssm start-session --target $INSTANCE_ID
   
   # Run stress test on the instance
   stress --cpu 4 --timeout 600s
   ```

2. **Monitor scaling events:**
   ```bash
   # Watch Auto Scaling activities
   ASG_NAME=$(cd terraform/environments/dev && terraform output -raw asg_name)
   aws autoscaling describe-scaling-activities --auto-scaling-group-name $ASG_NAME
   
   # Watch CloudWatch alarms
   aws cloudwatch describe-alarms --alarm-names \
     "taskmanager-dev-cpu-high" \
     "taskmanager-dev-cpu-low"
   ```

3. **Monitor target group health:**
   ```bash
   # Watch target health
   TG_ARN=$(cd terraform/environments/dev && terraform output -raw target_group_arn)
   
   while true; do
     aws elbv2 describe-target-health --target-group-arn $TG_ARN
     sleep 30
   done
   ```

### Task 3: Test Health Checks and Failover

1. **Simulate application failure:**
   ```bash
   # Stop application on one instance
   aws ssm send-command \
     --instance-ids $INSTANCE_ID \
     --document-name "AWS-RunShellScript" \
     --parameters 'commands=["docker stop taskmanager"]'
   ```

2. **Monitor health check response:**
   ```bash
   # Check target health
   aws elbv2 describe-target-health --target-group-arn $TG_ARN
   
   # Test application availability
   curl -f http://$ALB_DNS/health
   ```

3. **Test automatic recovery:**
   ```bash
   # The health check cron job should restart the container
   # Monitor the recovery process
   aws ssm send-command \
     --instance-ids $INSTANCE_ID \
     --document-name "AWS-RunShellScript" \
     --parameters 'commands=["docker ps | grep taskmanager"]'
   ```

### ✅ Verification

1. **Verify load balancing works:**
   ```bash
   # All requests should return 200
   for i in {1..5}; do
     curl -o /dev/null -s -w "%{http_code}\n" http://$ALB_DNS/health
   done
   ```

2. **Verify scaling policies:**
   ```bash
   aws autoscaling describe-policies \
     --auto-scaling-group-name $ASG_NAME
   ```

3. **Verify monitoring dashboard:**
   ```bash
   aws cloudwatch get-dashboard \
     --dashboard-name "taskmanager-dev-dashboard"
   ```

---

## Summary

In this lab, you have successfully:

✅ **Created Application Load Balancer infrastructure:**
- Implemented ALB with proper health checks and access logging
- Configured target groups with sticky sessions
- Set up HTTP/HTTPS listeners with SSL termination

✅ **Designed scalable compute infrastructure:**
- Created EC2 launch templates with proper IAM roles
- Implemented Auto Scaling Groups with scaling policies
- Configured user data scripts for automated deployment

✅ **Implemented comprehensive monitoring:**
- Set up CloudWatch alarms for CPU utilization
- Created CloudWatch dashboard for visualization
- Implemented ECR repository with lifecycle policies

✅ **Deployed and tested load balancing:**
- Successfully deployed compute infrastructure to AWS
- Built and pushed Docker images to ECR
- Tested load balancer functionality and health checks

✅ **Validated scaling and failover:**
- Tested auto-scaling behavior under load
- Verified health check and failover mechanisms
- Confirmed application recovery and high availability

## Next Steps

Your compute infrastructure is now highly available and scalable. In the next lab, you will:

- Implement CI/CD pipeline with GitHub Actions
- Set up automated testing and security scanning
- Create multi-environment deployment workflows
- Implement blue-green deployment strategies

## Troubleshooting

### Common Issues

**Issue:** Target group health checks failing
**Solution:**
- Verify security group allows ALB to reach instances on port 5000
- Check that health endpoint `/health` returns 200 status code
- Ensure application is running on all instances

**Issue:** Auto Scaling not working
**Solution:**
- Check CloudWatch alarms are configured correctly
- Verify scaling policies have proper thresholds
- Ensure IAM roles have necessary permissions

**Issue:** Cannot access application through ALB
**Solution:**
- Verify ALB security group allows HTTP/HTTPS traffic
- Check target group has healthy targets
- Ensure DNS resolution is working

### Additional Resources

- [AWS ALB Documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/)
- [Auto Scaling Documentation](https://docs.aws.amazon.com/autoscaling/ec2/userguide/)
- [CloudWatch Monitoring](https://docs.aws.amazon.com/cloudwatch/)

---

**🎉 Congratulations!** You have successfully completed Lab 04. Your application now has a highly available, scalable compute infrastructure with load balancing and auto-scaling capabilities.

**Next:** [Lab 05: CI/CD Pipeline Implementation](./05-cicd-pipeline-implementation.md)