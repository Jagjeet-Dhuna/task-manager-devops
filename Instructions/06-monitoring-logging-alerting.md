# Lab 06: Monitoring, Logging, and Alerting

## Overview

In this lab, you will implement a comprehensive monitoring, logging, and alerting system for your multi-environment application. You'll set up CloudWatch metrics, create centralized logging, build monitoring dashboards, and configure automated alerting to ensure optimal application performance and quick incident response.

## Objectives

After completing this lab, you will be able to:
- Configure CloudWatch metrics and custom metrics collection
- Set up centralized logging with CloudWatch Logs
- Create comprehensive monitoring dashboards
- Implement automated alerting and notification systems
- Set up log aggregation and analysis tools

## Prerequisites

- Completed Lab 05 (CI/CD Pipeline Implementation)
- Understanding of monitoring and observability concepts
- Basic knowledge of AWS CloudWatch services
- Existing application infrastructure deployed

## Duration

**Estimated Time:** 60 minutes

---

## Exercise 1: Configure CloudWatch Metrics and Alarms

### Task 1: Create Enhanced CloudWatch Agent Configuration

1. **Create `terraform/modules/monitoring/cloudwatch-agent.tf`:**
   ```hcl
   # CloudWatch Agent Configuration
   resource "aws_ssm_parameter" "cloudwatch_agent_config" {
     name  = "/AmazonCloudWatch-Agent/${var.project_name}-${var.environment}"
     type  = "String"
     value = jsonencode({
       agent = {
         metrics_collection_interval = 60
         run_as_user = "cwagent"
       }
       logs = {
         logs_collected = {
           files = {
             collect_list = [
               {
                 file_path = "/var/log/messages"
                 log_group_name = "/aws/ec2/${var.project_name}-${var.environment}/system"
                 log_stream_name = "{instance_id}/system"
                 timestamp_format = "%b %d %H:%M:%S"
               },
               {
                 file_path = "/var/log/docker"
                 log_group_name = "/aws/ec2/${var.project_name}-${var.environment}/docker"
                 log_stream_name = "{instance_id}/docker"
                 timestamp_format = "%Y-%m-%dT%H:%M:%S.%f"
               },
               {
                 file_path = "/opt/app/logs/app.log"
                 log_group_name = "/aws/application/${var.project_name}-${var.environment}"
                 log_stream_name = "{instance_id}/application"
                 timestamp_format = "%Y-%m-%d %H:%M:%S"
               }
             ]
           }
         }
       }
       metrics = {
         namespace = "TaskManager/${var.environment}"
         metrics_collected = {
           cpu = {
             measurement = [
               "cpu_usage_idle",
               "cpu_usage_iowait",
               "cpu_usage_user",
               "cpu_usage_system"
             ]
             metrics_collection_interval = 60
             totalcpu = false
           }
           disk = {
             measurement = [
               "used_percent"
             ]
             metrics_collection_interval = 60
             resources = [
               "*"
             ]
           }
           diskio = {
             measurement = [
               "io_time",
               "read_bytes",
               "write_bytes",
               "reads",
               "writes"
             ]
             metrics_collection_interval = 60
             resources = [
               "*"
             ]
           }
           mem = {
             measurement = [
               "mem_used_percent"
             ]
             metrics_collection_interval = 60
           }
           netstat = {
             measurement = [
               "tcp_established",
               "tcp_time_wait"
             ]
             metrics_collection_interval = 60
           }
           processes = {
             measurement = [
               "running",
               "sleeping",
               "dead"
             ]
             metrics_collection_interval = 60
           }
         }
       }
     })
   
     tags = {
       Name = "${var.project_name}-${var.environment}-cw-agent-config"
       Environment = var.environment
     }
   }
   
   # CloudWatch Log Groups
   resource "aws_cloudwatch_log_group" "system" {
     name              = "/aws/ec2/${var.project_name}-${var.environment}/system"
     retention_in_days = var.log_retention_days
   
     tags = {
       Name = "${var.project_name}-${var.environment}-system-logs"
       Environment = var.environment
     }
   }
   
   resource "aws_cloudwatch_log_group" "docker" {
     name              = "/aws/ec2/${var.project_name}-${var.environment}/docker"
     retention_in_days = var.log_retention_days
   
     tags = {
       Name = "${var.project_name}-${var.environment}-docker-logs"
       Environment = var.environment
     }
   }
   
   resource "aws_cloudwatch_log_group" "application" {
     name              = "/aws/application/${var.project_name}-${var.environment}"
     retention_in_days = var.log_retention_days
   
     tags = {
       Name = "${var.project_name}-${var.environment}-app-logs"
       Environment = var.environment
     }
   }
   
   # CloudWatch Log Groups for ALB
   resource "aws_cloudwatch_log_group" "alb" {
     name              = "/aws/elasticloadbalancing/${var.project_name}-${var.environment}"
     retention_in_days = var.log_retention_days
   
     tags = {
       Name = "${var.project_name}-${var.environment}-alb-logs"
       Environment = var.environment
     }
   }
   ```

### Task 2: Create Custom Metrics and Alarms

1. **Create `terraform/modules/monitoring/custom-metrics.tf`:**
   ```hcl
   # Application Performance Alarms
   resource "aws_cloudwatch_metric_alarm" "app_response_time" {
     alarm_name          = "${var.project_name}-${var.environment}-app-response-time"
     comparison_operator = "GreaterThanThreshold"
     evaluation_periods  = "2"
     metric_name         = "TargetResponseTime"
     namespace           = "AWS/ApplicationELB"
     period              = "300"
     statistic           = "Average"
     threshold           = "1.0"
     alarm_description   = "This metric monitors application response time"
     alarm_actions       = [aws_sns_topic.alerts.arn]
     ok_actions          = [aws_sns_topic.alerts.arn]
     treat_missing_data  = "notBreaching"
   
     dimensions = {
       LoadBalancer = var.alb_name
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-app-response-time-alarm"
       Environment = var.environment
     }
   }
   
   # Error Rate Alarm
   resource "aws_cloudwatch_metric_alarm" "app_error_rate" {
     alarm_name          = "${var.project_name}-${var.environment}-app-error-rate"
     comparison_operator = "GreaterThanThreshold"
     evaluation_periods  = "2"
     metric_name         = "HTTPCode_Target_5XX_Count"
     namespace           = "AWS/ApplicationELB"
     period              = "300"
     statistic           = "Sum"
     threshold           = "10"
     alarm_description   = "This metric monitors application error rate"
     alarm_actions       = [aws_sns_topic.alerts.arn]
     ok_actions          = [aws_sns_topic.alerts.arn]
     treat_missing_data  = "notBreaching"
   
     dimensions = {
       LoadBalancer = var.alb_name
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-app-error-rate-alarm"
       Environment = var.environment
     }
   }
   
   # Custom Application Metrics
   resource "aws_cloudwatch_metric_alarm" "custom_user_registrations" {
     alarm_name          = "${var.project_name}-${var.environment}-user-registrations"
     comparison_operator = "GreaterThanThreshold"
     evaluation_periods  = "1"
     metric_name         = "UserRegistrations"
     namespace           = "TaskManager/Application"
     period              = "900"
     statistic           = "Sum"
     threshold           = "100"
     alarm_description   = "High number of user registrations"
     alarm_actions       = [aws_sns_topic.alerts.arn]
     treat_missing_data  = "notBreaching"
   
     dimensions = {
       Environment = var.environment
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-user-registrations-alarm"
       Environment = var.environment
     }
   }
   
   # Database Connection Pool Alarm
   resource "aws_cloudwatch_metric_alarm" "db_connection_pool" {
     alarm_name          = "${var.project_name}-${var.environment}-db-connection-pool"
     comparison_operator = "GreaterThanThreshold"
     evaluation_periods  = "2"
     metric_name         = "DatabaseConnections"
     namespace           = "AWS/RDS"
     period              = "300"
     statistic           = "Average"
     threshold           = "80"
     alarm_description   = "High database connection usage"
     alarm_actions       = [aws_sns_topic.alerts.arn]
     ok_actions          = [aws_sns_topic.alerts.arn]
     treat_missing_data  = "notBreaching"
   
     dimensions = {
       DBInstanceIdentifier = var.db_instance_id
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-db-connection-pool-alarm"
       Environment = var.environment
     }
   }
   
   # Memory Usage Alarm
   resource "aws_cloudwatch_metric_alarm" "memory_usage" {
     alarm_name          = "${var.project_name}-${var.environment}-memory-usage"
     comparison_operator = "GreaterThanThreshold"
     evaluation_periods  = "2"
     metric_name         = "mem_used_percent"
     namespace           = "TaskManager/${var.environment}"
     period              = "300"
     statistic           = "Average"
     threshold           = "80"
     alarm_description   = "High memory usage"
     alarm_actions       = [aws_sns_topic.alerts.arn]
     ok_actions          = [aws_sns_topic.alerts.arn]
     treat_missing_data  = "notBreaching"
   
     dimensions = {
       AutoScalingGroupName = var.asg_name
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-memory-usage-alarm"
       Environment = var.environment
     }
   }
   
   # Disk Usage Alarm
   resource "aws_cloudwatch_metric_alarm" "disk_usage" {
     alarm_name          = "${var.project_name}-${var.environment}-disk-usage"
     comparison_operator = "GreaterThanThreshold"
     evaluation_periods  = "2"
     metric_name         = "used_percent"
     namespace           = "TaskManager/${var.environment}"
     period              = "300"
     statistic           = "Average"
     threshold           = "85"
     alarm_description   = "High disk usage"
     alarm_actions       = [aws_sns_topic.alerts.arn]
     ok_actions          = [aws_sns_topic.alerts.arn]
     treat_missing_data  = "notBreaching"
   
     dimensions = {
       AutoScalingGroupName = var.asg_name
       device = "/dev/xvda1"
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-disk-usage-alarm"
       Environment = var.environment
     }
   }
   ```

### Task 3: Create SNS Topics and Subscriptions

1. **Create `terraform/modules/monitoring/sns.tf`:**
   ```hcl
   # SNS Topic for Alerts
   resource "aws_sns_topic" "alerts" {
     name = "${var.project_name}-${var.environment}-alerts"
   
     tags = {
       Name = "${var.project_name}-${var.environment}-alerts"
       Environment = var.environment
     }
   }
   
   # SNS Topic Policy
   resource "aws_sns_topic_policy" "alerts_policy" {
     arn = aws_sns_topic.alerts.arn
   
     policy = jsonencode({
       Version = "2012-10-17"
       Statement = [
         {
           Effect = "Allow"
           Principal = {
             Service = "cloudwatch.amazonaws.com"
           }
           Action = "SNS:Publish"
           Resource = aws_sns_topic.alerts.arn
         }
       ]
     })
   }
   
   # Email Subscriptions
   resource "aws_sns_topic_subscription" "email_alerts" {
     count     = length(var.alert_email_addresses)
     topic_arn = aws_sns_topic.alerts.arn
     protocol  = "email"
     endpoint  = var.alert_email_addresses[count.index]
   }
   
   # Slack Webhook Subscription (if configured)
   resource "aws_sns_topic_subscription" "slack_alerts" {
     count     = var.slack_webhook_url != "" ? 1 : 0
     topic_arn = aws_sns_topic.alerts.arn
     protocol  = "https"
     endpoint  = var.slack_webhook_url
   }
   
   # PagerDuty Integration (if configured)
   resource "aws_sns_topic_subscription" "pagerduty_alerts" {
     count     = var.pagerduty_endpoint != "" ? 1 : 0
     topic_arn = aws_sns_topic.alerts.arn
     protocol  = "https"
     endpoint  = var.pagerduty_endpoint
   }
   
   # SMS Subscriptions for Critical Alerts
   resource "aws_sns_topic" "critical_alerts" {
     name = "${var.project_name}-${var.environment}-critical-alerts"
   
     tags = {
       Name = "${var.project_name}-${var.environment}-critical-alerts"
       Environment = var.environment
     }
   }
   
   resource "aws_sns_topic_subscription" "sms_critical_alerts" {
     count     = length(var.alert_phone_numbers)
     topic_arn = aws_sns_topic.critical_alerts.arn
     protocol  = "sms"
     endpoint  = var.alert_phone_numbers[count.index]
   }
   ```

### ✅ Verification

1. **Check CloudWatch Agent configuration:**
   ```bash
   aws ssm get-parameter --name "/AmazonCloudWatch-Agent/taskmanager-dev" --query 'Parameter.Value' --output text | jq .
   ```

2. **Verify SNS topics:**
   ```bash
   aws sns list-topics --query 'Topics[?contains(TopicArn, `taskmanager-dev-alerts`)]'
   ```

---

## Exercise 2: Set up Centralized Logging

### Task 1: Configure Application Logging

1. **Update application to use structured logging (`app.py`):**
   ```python
   import logging
   import json
   import os
   from datetime import datetime
   
   # Configure structured logging
   class StructuredLogger:
       def __init__(self, name):
           self.logger = logging.getLogger(name)
           self.logger.setLevel(logging.INFO)
           
           # Create formatter
           formatter = logging.Formatter(
               '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
           )
           
           # Console handler
           console_handler = logging.StreamHandler()
           console_handler.setFormatter(formatter)
           self.logger.addHandler(console_handler)
           
           # File handler
           os.makedirs('/opt/app/logs', exist_ok=True)
           file_handler = logging.FileHandler('/opt/app/logs/app.log')
           file_handler.setFormatter(formatter)
           self.logger.addHandler(file_handler)
   
       def log_event(self, level, message, **kwargs):
           event = {
               'timestamp': datetime.utcnow().isoformat(),
               'level': level,
               'message': message,
               'environment': os.environ.get('ENVIRONMENT', 'dev'),
               'instance_id': os.environ.get('INSTANCE_ID', 'unknown'),
               **kwargs
           }
           
           if level == 'INFO':
               self.logger.info(json.dumps(event))
           elif level == 'ERROR':
               self.logger.error(json.dumps(event))
           elif level == 'WARNING':
               self.logger.warning(json.dumps(event))
           elif level == 'DEBUG':
               self.logger.debug(json.dumps(event))
   
   # Initialize logger
   app_logger = StructuredLogger('taskmanager')
   
   # Add to Flask app
   @app.before_request
   def log_request():
       app_logger.log_event(
           'INFO',
           'Request received',
           method=request.method,
           path=request.path,
           remote_addr=request.remote_addr,
           user_agent=request.headers.get('User-Agent')
       )
   
   @app.after_request
   def log_response(response):
       app_logger.log_event(
           'INFO',
           'Response sent',
           status_code=response.status_code,
           method=request.method,
           path=request.path
       )
       return response
   ```

### Task 2: Create Log Analysis Queries

1. **Create `terraform/modules/monitoring/log-insights.tf`:**
   ```hcl
   # CloudWatch Insights Queries
   resource "aws_cloudwatch_query_definition" "error_analysis" {
     name = "${var.project_name}-${var.environment}-error-analysis"
   
     log_group_names = [
       aws_cloudwatch_log_group.application.name
     ]
   
     query_string = <<EOF
   fields @timestamp, @message, level, message, method, path, status_code
   | filter level = "ERROR"
   | stats count() by method, path, status_code
   | sort @timestamp desc
   | limit 100
   EOF
   }
   
   resource "aws_cloudwatch_query_definition" "performance_analysis" {
     name = "${var.project_name}-${var.environment}-performance-analysis"
   
     log_group_names = [
       aws_cloudwatch_log_group.application.name
     ]
   
     query_string = <<EOF
   fields @timestamp, @message, method, path, response_time
   | filter method = "GET" or method = "POST"
   | filter response_time > 1000
   | stats avg(response_time), max(response_time), min(response_time) by path
   | sort avg(response_time) desc
   | limit 50
   EOF
   }
   
   resource "aws_cloudwatch_query_definition" "user_activity" {
     name = "${var.project_name}-${var.environment}-user-activity"
   
     log_group_names = [
       aws_cloudwatch_log_group.application.name
     ]
   
     query_string = <<EOF
   fields @timestamp, @message, user_id, action, resource
   | filter action = "CREATE" or action = "UPDATE" or action = "DELETE"
   | stats count() by user_id, action
   | sort count() desc
   | limit 100
   EOF
   }
   
   resource "aws_cloudwatch_query_definition" "security_events" {
     name = "${var.project_name}-${var.environment}-security-events"
   
     log_group_names = [
       aws_cloudwatch_log_group.application.name
     ]
   
     query_string = <<EOF
   fields @timestamp, @message, remote_addr, user_agent, path, status_code
   | filter status_code >= 400
   | stats count() by remote_addr, status_code
   | sort count() desc
   | limit 50
   EOF
   }
   ```

### Task 3: Create Log Retention and Archiving

1. **Create `terraform/modules/monitoring/log-archiving.tf`:**
   ```hcl
   # S3 Bucket for Log Archiving
   resource "aws_s3_bucket" "log_archive" {
     bucket = "${var.project_name}-${var.environment}-log-archive-${random_id.bucket_suffix.hex}"
   
     tags = {
       Name = "${var.project_name}-${var.environment}-log-archive"
       Environment = var.environment
     }
   }
   
   resource "random_id" "bucket_suffix" {
     byte_length = 8
   }
   
   # S3 Bucket Lifecycle Configuration
   resource "aws_s3_bucket_lifecycle_configuration" "log_archive_lifecycle" {
     bucket = aws_s3_bucket.log_archive.id
   
     rule {
       id     = "log_archive_lifecycle"
       status = "Enabled"
   
       transition {
         days          = 30
         storage_class = "STANDARD_IA"
       }
   
       transition {
         days          = 90
         storage_class = "GLACIER"
       }
   
       transition {
         days          = 365
         storage_class = "DEEP_ARCHIVE"
       }
   
       expiration {
         days = 2555  # 7 years
       }
     }
   }
   
   # CloudWatch Logs Destination for Kinesis
   resource "aws_kinesis_firehose_delivery_stream" "log_stream" {
     name        = "${var.project_name}-${var.environment}-log-stream"
     destination = "s3"
   
     s3_configuration {
       role_arn   = aws_iam_role.firehose_role.arn
       bucket_arn = aws_s3_bucket.log_archive.arn
       prefix     = "logs/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/"
       
       buffer_size     = 5
       buffer_interval = 300
       
       compression_format = "GZIP"
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-log-stream"
       Environment = var.environment
     }
   }
   
   # IAM Role for Kinesis Firehose
   resource "aws_iam_role" "firehose_role" {
     name = "${var.project_name}-${var.environment}-firehose-role"
   
     assume_role_policy = jsonencode({
       Version = "2012-10-17"
       Statement = [
         {
           Action = "sts:AssumeRole"
           Effect = "Allow"
           Principal = {
             Service = "firehose.amazonaws.com"
           }
         }
       ]
     })
   }
   
   resource "aws_iam_role_policy" "firehose_policy" {
     name = "${var.project_name}-${var.environment}-firehose-policy"
     role = aws_iam_role.firehose_role.id
   
     policy = jsonencode({
       Version = "2012-10-17"
       Statement = [
         {
           Effect = "Allow"
           Action = [
             "s3:AbortMultipartUpload",
             "s3:GetBucketLocation",
             "s3:GetObject",
             "s3:ListBucket",
             "s3:ListBucketMultipartUploads",
             "s3:PutObject"
           ]
           Resource = [
             aws_s3_bucket.log_archive.arn,
             "${aws_s3_bucket.log_archive.arn}/*"
           ]
         }
       ]
     })
   }
   
   # CloudWatch Logs Subscription Filter
   resource "aws_cloudwatch_log_subscription_filter" "app_logs_filter" {
     name            = "${var.project_name}-${var.environment}-app-logs-filter"
     log_group_name  = aws_cloudwatch_log_group.application.name
     filter_pattern  = ""
     destination_arn = aws_kinesis_firehose_delivery_stream.log_stream.arn
     role_arn        = aws_iam_role.logs_role.arn
   }
   
   # IAM Role for CloudWatch Logs
   resource "aws_iam_role" "logs_role" {
     name = "${var.project_name}-${var.environment}-logs-role"
   
     assume_role_policy = jsonencode({
       Version = "2012-10-17"
       Statement = [
         {
           Action = "sts:AssumeRole"
           Effect = "Allow"
           Principal = {
             Service = "logs.amazonaws.com"
           }
         }
       ]
     })
   }
   
   resource "aws_iam_role_policy" "logs_policy" {
     name = "${var.project_name}-${var.environment}-logs-policy"
     role = aws_iam_role.logs_role.id
   
     policy = jsonencode({
       Version = "2012-10-17"
       Statement = [
         {
           Effect = "Allow"
           Action = [
             "firehose:PutRecord",
             "firehose:PutRecordBatch"
           ]
           Resource = aws_kinesis_firehose_delivery_stream.log_stream.arn
         }
       ]
     })
   }
   ```

### ✅ Verification

1. **Check log groups:**
   ```bash
   aws logs describe-log-groups --log-group-name-prefix "/aws/application/taskmanager-dev"
   ```

2. **Test log ingestion:**
   ```bash
   aws logs put-log-events \
     --log-group-name "/aws/application/taskmanager-dev" \
     --log-stream-name "test-stream" \
     --log-events timestamp=$(date +%s000),message="Test log message"
   ```

---

## Exercise 3: Create Monitoring Dashboards

### Task 1: Create Comprehensive CloudWatch Dashboard

1. **Create `terraform/modules/monitoring/dashboard-comprehensive.tf`:**
   ```hcl
   # Comprehensive CloudWatch Dashboard
   resource "aws_cloudwatch_dashboard" "comprehensive" {
     dashboard_name = "${var.project_name}-${var.environment}-comprehensive"
   
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
               ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", var.alb_name],
               [".", "TargetResponseTime", ".", "."],
               [".", "HTTPCode_Target_2XX_Count", ".", "."],
               [".", "HTTPCode_Target_4XX_Count", ".", "."],
               [".", "HTTPCode_Target_5XX_Count", ".", "."]
             ]
             period = 300
             stat   = "Sum"
             region = var.aws_region
             title  = "Application Load Balancer Metrics"
             yAxis = {
               left = {
                 min = 0
               }
             }
           }
         },
         {
           type   = "metric"
           x      = 12
           y      = 0
           width  = 12
           height = 6
   
           properties = {
             metrics = [
               ["AWS/EC2", "CPUUtilization", "AutoScalingGroupName", var.asg_name],
               ["TaskManager/${var.environment}", "mem_used_percent", "AutoScalingGroupName", var.asg_name],
               [".", "used_percent", ".", ".", "device", "/dev/xvda1"]
             ]
             period = 300
             stat   = "Average"
             region = var.aws_region
             title  = "EC2 Instance Metrics"
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
               ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", var.db_instance_id],
               [".", "DatabaseConnections", ".", "."],
               [".", "ReadLatency", ".", "."],
               [".", "WriteLatency", ".", "."],
               [".", "ReadIOPS", ".", "."],
               [".", "WriteIOPS", ".", "."]
             ]
             period = 300
             stat   = "Average"
             region = var.aws_region
             title  = "RDS Database Metrics"
             yAxis = {
               left = {
                 min = 0
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
               ["TaskManager/Application", "UserRegistrations", "Environment", var.environment],
               [".", "TasksCreated", ".", "."],
               [".", "TasksCompleted", ".", "."],
               [".", "LoginAttempts", ".", "."],
               [".", "APIRequests", ".", "."]
             ]
             period = 300
             stat   = "Sum"
             region = var.aws_region
             title  = "Application Business Metrics"
             yAxis = {
               left = {
                 min = 0
               }
             }
           }
         },
         {
           type   = "log"
           x      = 0
           y      = 12
           width  = 24
           height = 6
   
           properties = {
             query = "SOURCE '${aws_cloudwatch_log_group.application.name}' | fields @timestamp, level, message\\n| filter level = \"ERROR\"\\n| sort @timestamp desc\\n| limit 20"
             region = var.aws_region
             title  = "Recent Application Errors"
           }
         }
       ]
     })
   }
   ```

### Task 2: Create Business Metrics Dashboard

1. **Create `terraform/modules/monitoring/dashboard-business.tf`:**
   ```hcl
   # Business Metrics Dashboard
   resource "aws_cloudwatch_dashboard" "business_metrics" {
     dashboard_name = "${var.project_name}-${var.environment}-business-metrics"
   
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
               ["TaskManager/Application", "ActiveUsers", "Environment", var.environment],
               [".", "NewUsers", ".", "."],
               [".", "UserRetention", ".", "."]
             ]
             period = 3600
             stat   = "Average"
             region = var.aws_region
             title  = "User Metrics"
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
               ["TaskManager/Application", "TasksCreated", "Environment", var.environment],
               [".", "TasksCompleted", ".", "."],
               [".", "TaskCompletionRate", ".", "."]
             ]
             period = 3600
             stat   = "Sum"
             region = var.aws_region
             title  = "Task Metrics"
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
               ["TaskManager/Application", "APIRequests", "Environment", var.environment],
               [".", "APIErrors", ".", "."],
               [".", "APISuccessRate", ".", "."]
             ]
             period = 3600
             stat   = "Sum"
             region = var.aws_region
             title  = "API Metrics"
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
               ["TaskManager/Application", "ConversionRate", "Environment", var.environment],
               [".", "EngagementScore", ".", "."],
               [".", "FeatureUsage", ".", "."]
             ]
             period = 3600
             stat   = "Average"
             region = var.aws_region
             title  = "Engagement Metrics"
             yAxis = {
               left = {
                 min = 0
                 max = 100
               }
             }
           }
         },
         {
           type   = "log"
           x      = 12
           y      = 6
           width  = 12
           height = 6
   
           properties = {
             query = "SOURCE '${aws_cloudwatch_log_group.application.name}' | fields @timestamp, user_id, action, resource\\n| filter action = \"CREATE\" or action = \"UPDATE\" or action = \"DELETE\"\\n| stats count() by user_id\\n| sort count() desc\\n| limit 10"
             region = var.aws_region
             title  = "Most Active Users"
           }
         }
       ]
     })
   }
   ```

### Task 3: Create Performance Dashboard

1. **Create `terraform/modules/monitoring/dashboard-performance.tf`:**
   ```hcl
   # Performance Dashboard
   resource "aws_cloudwatch_dashboard" "performance" {
     dashboard_name = "${var.project_name}-${var.environment}-performance"
   
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
               [".", "NewConnectionCount", ".", "."],
               [".", "ActiveConnectionCount", ".", "."]
             ]
             period = 300
             stat   = "Average"
             region = var.aws_region
             title  = "Load Balancer Performance"
             yAxis = {
               left = {
                 min = 0
               }
             }
           }
         },
         {
           type   = "metric"
           x      = 12
           y      = 0
           width  = 12
           height = 6
   
           properties = {
             metrics = [
               ["AWS/RDS", "ReadLatency", "DBInstanceIdentifier", var.db_instance_id],
               [".", "WriteLatency", ".", "."],
               [".", "ReadThroughput", ".", "."],
               [".", "WriteThroughput", ".", "."]
             ]
             period = 300
             stat   = "Average"
             region = var.aws_region
             title  = "Database Performance"
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
           width  = 8
           height = 6
   
           properties = {
             metrics = [
               ["TaskManager/${var.environment}", "tcp_established", "AutoScalingGroupName", var.asg_name],
               [".", "tcp_time_wait", ".", "."],
               [".", "processes_running", ".", "."],
               [".", "processes_sleeping", ".", "."]
             ]
             period = 300
             stat   = "Average"
             region = var.aws_region
             title  = "System Performance"
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
           y      = 6
           width  = 8
           height = 6
   
           properties = {
             metrics = [
               ["TaskManager/${var.environment}", "io_time", "AutoScalingGroupName", var.asg_name],
               [".", "read_bytes", ".", "."],
               [".", "write_bytes", ".", "."]
             ]
             period = 300
             stat   = "Average"
             region = var.aws_region
             title  = "I/O Performance"
             yAxis = {
               left = {
                 min = 0
               }
             }
           }
         },
         {
           type   = "log"
           x      = 16
           y      = 6
           width  = 8
           height = 6
   
           properties = {
             query = "SOURCE '${aws_cloudwatch_log_group.application.name}' | fields @timestamp, method, path, response_time\\n| filter response_time > 1000\\n| stats avg(response_time), max(response_time), count() by path\\n| sort avg(response_time) desc\\n| limit 10"
             region = var.aws_region
             title  = "Slow Requests"
           }
         }
       ]
     })
   }
   ```

### ✅ Verification

1. **Check dashboards:**
   ```bash
   aws cloudwatch list-dashboards --query 'DashboardEntries[?contains(DashboardName, `taskmanager-dev`)]'
   ```

2. **View dashboard:**
   ```bash
   aws cloudwatch get-dashboard --dashboard-name "taskmanager-dev-comprehensive"
   ```

---

## Exercise 4: Implement Automated Alerting and Notifications

### Task 1: Create Alert Escalation Policies

1. **Create `terraform/modules/monitoring/alert-escalation.tf`:**
   ```hcl
   # Alert Escalation Configuration
   locals {
     alert_escalation = {
       critical = {
         initial_delay = 0
         escalation_delay = 300  # 5 minutes
         max_escalations = 3
         notification_channels = [
           aws_sns_topic.critical_alerts.arn,
           aws_sns_topic.alerts.arn
         ]
       }
       warning = {
         initial_delay = 600  # 10 minutes
         escalation_delay = 1800  # 30 minutes
         max_escalations = 2
         notification_channels = [
           aws_sns_topic.alerts.arn
         ]
       }
       info = {
         initial_delay = 3600  # 1 hour
         escalation_delay = 7200  # 2 hours
         max_escalations = 1
         notification_channels = [
           aws_sns_topic.alerts.arn
         ]
       }
     }
   }
   
   # Critical Application Down Alarm
   resource "aws_cloudwatch_metric_alarm" "app_down" {
     alarm_name          = "${var.project_name}-${var.environment}-app-down"
     comparison_operator = "LessThanThreshold"
     evaluation_periods  = "2"
     metric_name         = "HealthyHostCount"
     namespace           = "AWS/ApplicationELB"
     period              = "60"
     statistic           = "Average"
     threshold           = "1"
     alarm_description   = "Application is down - no healthy hosts"
     alarm_actions       = [aws_sns_topic.critical_alerts.arn]
     ok_actions          = [aws_sns_topic.alerts.arn]
     treat_missing_data  = "breaching"
   
     dimensions = {
       TargetGroup  = var.target_group_name
       LoadBalancer = var.alb_name
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-app-down-alarm"
       Environment = var.environment
       Severity = "Critical"
     }
   }
   
   # Database Down Alarm
   resource "aws_cloudwatch_metric_alarm" "db_down" {
     alarm_name          = "${var.project_name}-${var.environment}-db-down"
     comparison_operator = "LessThanThreshold"
     evaluation_periods  = "2"
     metric_name         = "DatabaseConnections"
     namespace           = "AWS/RDS"
     period              = "60"
     statistic           = "Average"
     threshold           = "1"
     alarm_description   = "Database is not accepting connections"
     alarm_actions       = [aws_sns_topic.critical_alerts.arn]
     ok_actions          = [aws_sns_topic.alerts.arn]
     treat_missing_data  = "breaching"
   
     dimensions = {
       DBInstanceIdentifier = var.db_instance_id
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-db-down-alarm"
       Environment = var.environment
       Severity = "Critical"
     }
   }
   
   # High Error Rate Alarm
   resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
     alarm_name          = "${var.project_name}-${var.environment}-high-error-rate"
     comparison_operator = "GreaterThanThreshold"
     evaluation_periods  = "3"
     metric_name         = "HTTPCode_Target_5XX_Count"
     namespace           = "AWS/ApplicationELB"
     period              = "300"
     statistic           = "Sum"
     threshold           = "50"
     alarm_description   = "High error rate detected"
     alarm_actions       = [aws_sns_topic.critical_alerts.arn]
     ok_actions          = [aws_sns_topic.alerts.arn]
     treat_missing_data  = "notBreaching"
   
     dimensions = {
       LoadBalancer = var.alb_name
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-high-error-rate-alarm"
       Environment = var.environment
       Severity = "Critical"
     }
   }
   ```

### Task 2: Create Notification Templates

1. **Create `terraform/modules/monitoring/notification-templates.tf`:**
   ```hcl
   # Lambda Function for Custom Notifications
   resource "aws_lambda_function" "alert_processor" {
     filename         = "${path.module}/alert_processor.zip"
     function_name    = "${var.project_name}-${var.environment}-alert-processor"
     role            = aws_iam_role.alert_processor_role.arn
     handler         = "index.handler"
     runtime         = "python3.9"
     timeout         = 30
   
     environment {
       variables = {
         SLACK_WEBHOOK_URL = var.slack_webhook_url
         ENVIRONMENT = var.environment
         PROJECT_NAME = var.project_name
       }
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-alert-processor"
       Environment = var.environment
     }
   }
   
   # Create Lambda deployment package
   data "archive_file" "alert_processor" {
     type        = "zip"
     output_path = "${path.module}/alert_processor.zip"
     source {
       content = <<EOF
   import json
   import urllib3
   import os
   
   def handler(event, context):
       webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
       environment = os.environ.get('ENVIRONMENT')
       project_name = os.environ.get('PROJECT_NAME')
       
       if not webhook_url:
           return {'statusCode': 200, 'body': 'No webhook URL configured'}
       
       # Parse SNS message
       message = json.loads(event['Records'][0]['Sns']['Message'])
       
       # Extract alarm details
       alarm_name = message.get('AlarmName', 'Unknown')
       alarm_description = message.get('AlarmDescription', 'No description')
       new_state = message.get('NewStateValue', 'Unknown')
       old_state = message.get('OldStateValue', 'Unknown')
       reason = message.get('NewStateReason', 'No reason provided')
       
       # Determine color based on state
       color = {
           'ALARM': 'danger',
           'OK': 'good',
           'INSUFFICIENT_DATA': 'warning'
       }.get(new_state, 'warning')
       
       # Create Slack message
       slack_message = {
           'text': f'CloudWatch Alarm: {alarm_name}',
           'attachments': [
               {
                   'color': color,
                   'title': f'{project_name} - {environment}',
                   'fields': [
                       {
                           'title': 'Alarm',
                           'value': alarm_name,
                           'short': True
                       },
                       {
                           'title': 'State',
                           'value': f'{old_state} → {new_state}',
                           'short': True
                       },
                       {
                           'title': 'Description',
                           'value': alarm_description,
                           'short': False
                       },
                       {
                           'title': 'Reason',
                           'value': reason,
                           'short': False
                       }
                   ],
                   'footer': 'AWS CloudWatch',
                   'ts': int(context.aws_request_id.split('-')[0], 16)
               }
           ]
       }
       
       # Send to Slack
       http = urllib3.PoolManager()
       response = http.request(
           'POST',
           webhook_url,
           headers={'Content-Type': 'application/json'},
           body=json.dumps(slack_message)
       )
       
       return {
           'statusCode': 200,
           'body': json.dumps('Alert sent to Slack')
       }
   EOF
       filename = "index.py"
     }
   }
   
   # IAM Role for Lambda
   resource "aws_iam_role" "alert_processor_role" {
     name = "${var.project_name}-${var.environment}-alert-processor-role"
   
     assume_role_policy = jsonencode({
       Version = "2012-10-17"
       Statement = [
         {
           Action = "sts:AssumeRole"
           Effect = "Allow"
           Principal = {
             Service = "lambda.amazonaws.com"
           }
         }
       ]
     })
   }
   
   resource "aws_iam_role_policy" "alert_processor_policy" {
     name = "${var.project_name}-${var.environment}-alert-processor-policy"
     role = aws_iam_role.alert_processor_role.id
   
     policy = jsonencode({
       Version = "2012-10-17"
       Statement = [
         {
           Effect = "Allow"
           Action = [
             "logs:CreateLogGroup",
             "logs:CreateLogStream",
             "logs:PutLogEvents"
           ]
           Resource = "arn:aws:logs:*:*:*"
         }
       ]
     })
   }
   
   # SNS Topic Subscription for Lambda
   resource "aws_sns_topic_subscription" "alert_processor" {
     topic_arn = aws_sns_topic.alerts.arn
     protocol  = "lambda"
     endpoint  = aws_lambda_function.alert_processor.arn
   }
   
   # Lambda Permission for SNS
   resource "aws_lambda_permission" "sns_invoke" {
     statement_id  = "AllowExecutionFromSNS"
     action        = "lambda:InvokeFunction"
     function_name = aws_lambda_function.alert_processor.function_name
     principal     = "sns.amazonaws.com"
     source_arn    = aws_sns_topic.alerts.arn
   }
   ```

### Task 3: Create On-Call Rotation

1. **Create `terraform/modules/monitoring/on-call.tf`:**
   ```hcl
   # On-Call Schedule using EventBridge
   resource "aws_cloudwatch_event_rule" "on_call_rotation" {
     name        = "${var.project_name}-${var.environment}-on-call-rotation"
     description = "On-call rotation schedule"
     
     schedule_expression = "cron(0 9 ? * MON *)"  # Every Monday at 9 AM
   
     tags = {
       Name = "${var.project_name}-${var.environment}-on-call-rotation"
       Environment = var.environment
     }
   }
   
   # Lambda for On-Call Rotation
   resource "aws_lambda_function" "on_call_rotation" {
     filename         = "${path.module}/on_call_rotation.zip"
     function_name    = "${var.project_name}-${var.environment}-on-call-rotation"
     role            = aws_iam_role.on_call_role.arn
     handler         = "index.handler"
     runtime         = "python3.9"
     timeout         = 30
   
     environment {
       variables = {
         SNS_TOPIC_ARN = aws_sns_topic.critical_alerts.arn
         ENVIRONMENT = var.environment
         PROJECT_NAME = var.project_name
       }
     }
   
     tags = {
       Name = "${var.project_name}-${var.environment}-on-call-rotation"
       Environment = var.environment
     }
   }
   
   # On-Call Lambda Code
   data "archive_file" "on_call_rotation" {
     type        = "zip"
     output_path = "${path.module}/on_call_rotation.zip"
     source {
       content = <<EOF
   import json
   import boto3
   import os
   from datetime import datetime, timedelta
   
   def handler(event, context):
       sns = boto3.client('sns')
       topic_arn = os.environ.get('SNS_TOPIC_ARN')
       
       # On-call schedule (example)
       on_call_schedule = [
           {'name': 'DevOps Team A', 'phone': '+1234567890', 'email': 'team-a@example.com'},
           {'name': 'DevOps Team B', 'phone': '+1234567891', 'email': 'team-b@example.com'},
           {'name': 'DevOps Team C', 'phone': '+1234567892', 'email': 'team-c@example.com'}
       ]
       
       # Calculate current week
       current_week = datetime.now().isocalendar()[1]
       on_call_index = current_week % len(on_call_schedule)
       current_on_call = on_call_schedule[on_call_index]
       
       # Update SNS topic subscriptions
       # Remove old subscriptions
       paginator = sns.get_paginator('list_subscriptions_by_topic')
       for page in paginator.paginate(TopicArn=topic_arn):
           for subscription in page['Subscriptions']:
               if subscription['Protocol'] == 'sms':
                   sns.unsubscribe(SubscriptionArn=subscription['SubscriptionArn'])
       
       # Add new on-call person
       sns.subscribe(
           TopicArn=topic_arn,
           Protocol='sms',
           Endpoint=current_on_call['phone']
       )
       
       # Send notification about rotation
       message = f"On-call rotation updated. Current on-call: {current_on_call['name']}"
       sns.publish(
           TopicArn=topic_arn,
           Message=message,
           Subject=f"On-call rotation - Week {current_week}"
       )
       
       return {
           'statusCode': 200,
           'body': json.dumps(f"On-call updated to {current_on_call['name']}")
       }
   EOF
       filename = "index.py"
     }
   }
   
   # IAM Role for On-Call Lambda
   resource "aws_iam_role" "on_call_role" {
     name = "${var.project_name}-${var.environment}-on-call-role"
   
     assume_role_policy = jsonencode({
       Version = "2012-10-17"
       Statement = [
         {
           Action = "sts:AssumeRole"
           Effect = "Allow"
           Principal = {
             Service = "lambda.amazonaws.com"
           }
         }
       ]
     })
   }
   
   resource "aws_iam_role_policy" "on_call_policy" {
     name = "${var.project_name}-${var.environment}-on-call-policy"
     role = aws_iam_role.on_call_role.id
   
     policy = jsonencode({
       Version = "2012-10-17"
       Statement = [
         {
           Effect = "Allow"
           Action = [
             "logs:CreateLogGroup",
             "logs:CreateLogStream",
             "logs:PutLogEvents",
             "sns:Subscribe",
             "sns:Unsubscribe",
             "sns:ListSubscriptionsByTopic",
             "sns:Publish"
           ]
           Resource = "*"
         }
       ]
     })
   }
   
   # EventBridge Target
   resource "aws_cloudwatch_event_target" "on_call_target" {
     rule      = aws_cloudwatch_event_rule.on_call_rotation.name
     target_id = "OnCallRotationTarget"
     arn       = aws_lambda_function.on_call_rotation.arn
   }
   
   # Lambda Permission for EventBridge
   resource "aws_lambda_permission" "eventbridge_invoke" {
     statement_id  = "AllowExecutionFromEventBridge"
     action        = "lambda:InvokeFunction"
     function_name = aws_lambda_function.on_call_rotation.function_name
     principal     = "events.amazonaws.com"
     source_arn    = aws_cloudwatch_event_rule.on_call_rotation.arn
   }
   ```

### ✅ Verification

1. **Test SNS notifications:**
   ```bash
   aws sns publish \
     --topic-arn $(aws sns list-topics --query 'Topics[?contains(TopicArn, `taskmanager-dev-alerts`)].TopicArn' --output text) \
     --message "Test alert message"
   ```

2. **Check Lambda functions:**
   ```bash
   aws lambda list-functions --query 'Functions[?contains(FunctionName, `taskmanager-dev-alert`)]'
   ```

---

## Exercise 5: Test Monitoring and Alerting Scenarios

### Task 1: Create Test Scripts for Monitoring

1. **Create `scripts/monitoring-tests.sh`:**
   ```bash
   #!/bin/bash
   
   set -e
   
   PROJECT_NAME="taskmanager"
   ENVIRONMENT="dev"
   
   echo "Testing monitoring and alerting scenarios..."
   
   # Test 1: Simulate high CPU usage
   echo "Test 1: Simulating high CPU usage"
   ASG_NAME=$(aws autoscaling describe-auto-scaling-groups \
     --query "AutoScalingGroups[?contains(AutoScalingGroupName, '$PROJECT_NAME-$ENVIRONMENT')].AutoScalingGroupName" \
     --output text)
   
   if [ -n "$ASG_NAME" ]; then
     INSTANCE_ID=$(aws autoscaling describe-auto-scaling-groups \
       --auto-scaling-group-names $ASG_NAME \
       --query 'AutoScalingGroups[0].Instances[0].InstanceId' \
       --output text)
     
     echo "Running CPU stress test on instance: $INSTANCE_ID"
     aws ssm send-command \
       --instance-ids $INSTANCE_ID \
       --document-name "AWS-RunShellScript" \
       --parameters 'commands=["yum install -y stress", "stress --cpu 2 --timeout 300s &"]'
   fi
   
   # Test 2: Simulate application errors
   echo "Test 2: Simulating application errors"
   ALB_DNS=$(aws elbv2 describe-load-balancers \
     --query "LoadBalancers[?contains(LoadBalancerName, '$PROJECT_NAME-$ENVIRONMENT')].DNSName" \
     --output text)
   
   if [ -n "$ALB_DNS" ]; then
     echo "Generating error requests to: $ALB_DNS"
     for i in {1..20}; do
       curl -s -o /dev/null -w "%{http_code}\n" "http://$ALB_DNS/nonexistent-endpoint" &
     done
     wait
   fi
   
   # Test 3: Simulate memory pressure
   echo "Test 3: Simulating memory pressure"
   if [ -n "$INSTANCE_ID" ]; then
     echo "Running memory stress test on instance: $INSTANCE_ID"
     aws ssm send-command \
       --instance-ids $INSTANCE_ID \
       --document-name "AWS-RunShellScript" \
       --parameters 'commands=["stress --vm 1 --vm-bytes 500M --timeout 300s &"]'
   fi
   
   # Test 4: Check alarm states
   echo "Test 4: Checking alarm states"
   aws cloudwatch describe-alarms \
     --alarm-names "${PROJECT_NAME}-${ENVIRONMENT}-cpu-high" \
     --query 'MetricAlarms[0].StateValue' \
     --output text
   
   # Test 5: Simulate database connection issues
   echo "Test 5: Simulating database connection pressure"
   if [ -n "$ALB_DNS" ]; then
     echo "Generating concurrent database requests"
     for i in {1..50}; do
       curl -s -o /dev/null "http://$ALB_DNS/api/users" &
       curl -s -o /dev/null "http://$ALB_DNS/api/tasks" &
     done
     wait
   fi
   
   echo "Monitoring tests completed. Check CloudWatch for alarm states and notifications."
   ```

2. **Create `scripts/dashboard-validation.sh`:**
   ```bash
   #!/bin/bash
   
   set -e
   
   PROJECT_NAME="taskmanager"
   ENVIRONMENT="dev"
   
   echo "Validating monitoring dashboards..."
   
   # Check if dashboards exist
   DASHBOARDS=$(aws cloudwatch list-dashboards \
     --query "DashboardEntries[?contains(DashboardName, '$PROJECT_NAME-$ENVIRONMENT')].DashboardName" \
     --output text)
   
   if [ -z "$DASHBOARDS" ]; then
     echo "❌ No dashboards found for $PROJECT_NAME-$ENVIRONMENT"
     exit 1
   fi
   
   echo "✅ Found dashboards: $DASHBOARDS"
   
   # Validate each dashboard
   for dashboard in $DASHBOARDS; do
     echo "Validating dashboard: $dashboard"
     
     # Get dashboard configuration
     DASHBOARD_BODY=$(aws cloudwatch get-dashboard \
       --dashboard-name "$dashboard" \
       --query 'DashboardBody' \
       --output text)
     
     # Check if dashboard has widgets
     WIDGET_COUNT=$(echo "$DASHBOARD_BODY" | jq '.widgets | length')
     
     if [ "$WIDGET_COUNT" -gt 0 ]; then
       echo "✅ Dashboard $dashboard has $WIDGET_COUNT widgets"
     else
       echo "❌ Dashboard $dashboard has no widgets"
     fi
   done
   
   # Check CloudWatch Insights queries
   echo "Checking CloudWatch Insights queries..."
   QUERIES=$(aws logs describe-query-definitions \
     --query "QueryDefinitions[?contains(Name, '$PROJECT_NAME-$ENVIRONMENT')].Name" \
     --output text)
   
   if [ -n "$QUERIES" ]; then
     echo "✅ Found CloudWatch Insights queries: $QUERIES"
   else
     echo "❌ No CloudWatch Insights queries found"
   fi
   
   echo "Dashboard validation completed."
   ```

3. **Make scripts executable:**
   ```bash
   chmod +x scripts/monitoring-tests.sh
   chmod +x scripts/dashboard-validation.sh
   ```

### Task 2: Run Monitoring Tests

1. **Deploy monitoring infrastructure:**
   ```bash
   cd terraform/environments/dev
   terraform apply -target=module.monitoring
   ```

2. **Run monitoring tests:**
   ```bash
   ./scripts/monitoring-tests.sh
   ```

3. **Validate dashboards:**
   ```bash
   ./scripts/dashboard-validation.sh
   ```

### Task 3: Verify Alert Notifications

1. **Check alarm states:**
   ```bash
   aws cloudwatch describe-alarms \
     --alarm-name-prefix "taskmanager-dev" \
     --query 'MetricAlarms[*].[AlarmName,StateValue,StateReason]' \
     --output table
   ```

2. **Test SNS notifications:**
   ```bash
   TOPIC_ARN=$(aws sns list-topics --query 'Topics[?contains(TopicArn, `taskmanager-dev-alerts`)].TopicArn' --output text)
   
   aws sns publish \
     --topic-arn $TOPIC_ARN \
     --message "Test critical alert - monitoring system working" \
     --subject "Critical Alert Test"
   ```

3. **Check CloudWatch Logs:**
   ```bash
   aws logs describe-log-groups \
     --log-group-name-prefix "/aws/application/taskmanager-dev" \
     --query 'logGroups[*].[logGroupName,storedBytes,retentionInDays]' \
     --output table
   ```

### ✅ Verification

1. **All alarms configured:**
   ```bash
   aws cloudwatch describe-alarms \
     --alarm-name-prefix "taskmanager-dev" \
     --query 'length(MetricAlarms)'
   ```

2. **Dashboards accessible:**
   ```bash
   aws cloudwatch list-dashboards \
     --query 'DashboardEntries[?contains(DashboardName, `taskmanager-dev`)].DashboardName'
   ```

3. **Log groups created:**
   ```bash
   aws logs describe-log-groups \
     --log-group-name-prefix "/aws/application/taskmanager-dev" \
     --query 'logGroups[*].logGroupName'
   ```

---

## Summary

In this lab, you have successfully:

✅ **Configured comprehensive CloudWatch monitoring:**
- Set up CloudWatch Agent with custom metrics collection
- Created detailed system and application metrics
- Implemented custom business metrics tracking

✅ **Established centralized logging system:**
- Configured structured application logging
- Set up log aggregation and archiving
- Created CloudWatch Insights queries for log analysis

✅ **Built comprehensive monitoring dashboards:**
- Created business metrics dashboard
- Implemented performance monitoring dashboard
- Set up real-time operational dashboards

✅ **Implemented automated alerting system:**
- Configured multi-level alert escalation
- Set up custom notification templates
- Created on-call rotation management

✅ **Tested monitoring and alerting scenarios:**
- Validated monitoring system functionality
- Tested alert notification delivery
- Verified dashboard accuracy and completeness

## Next Steps

Your monitoring and alerting system is now fully operational. In the final lab, you will:

- Deploy staging and production environments
- Implement environment promotion workflows
- Set up cross-environment monitoring
- Create disaster recovery procedures

## Troubleshooting

### Common Issues

**Issue:** CloudWatch Agent not collecting metrics
**Solution:**
- Check IAM permissions for CloudWatch Agent
- Verify agent configuration in SSM Parameter Store
- Restart CloudWatch Agent service on EC2 instances

**Issue:** Alarms not triggering notifications
**Solution:**
- Verify SNS topic permissions
- Check alarm threshold settings
- Confirm subscription endpoints are confirmed

**Issue:** Dashboards showing no data
**Solution:**
- Verify metric namespaces and dimensions
- Check time range and region settings
- Confirm data sources are publishing metrics

### Additional Resources

- [CloudWatch Agent Documentation](https://docs.aws.amazon.com/cloudwatch/latest/monitoring/Install-CloudWatch-Agent.html)
- [CloudWatch Alarms Best Practices](https://docs.aws.amazon.com/cloudwatch/latest/monitoring/cloudwatch_concepts.html)
- [CloudWatch Insights Query Syntax](https://docs.aws.amazon.com/cloudwatch/latest/logs/CWL_QuerySyntax.html)

---

**🎉 Congratulations!** You have successfully completed Lab 06. Your application now has comprehensive monitoring, logging, and alerting capabilities that will help you maintain high availability and quickly respond to incidents.

**Next:** [Lab 07: Multi-Environment Deployment and Management](./07-multi-environment-deployment-management.md)