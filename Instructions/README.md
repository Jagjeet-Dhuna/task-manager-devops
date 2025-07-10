# Multi-Environment Web App Deployment - Lab Instructions

## Overview

This repository contains comprehensive lab instructions for deploying a Flask web application across multiple environments using modern DevOps practices. The labs are designed in Microsoft's hands-on lab format with detailed step-by-step instructions.

## Prerequisites

Before starting any lab, ensure you have:
- AWS Account with appropriate permissions
- GitHub account
- Local development environment set up
- Basic understanding of command line operations

## Lab Structure

### **Lab 01: Environment Setup and Application Containerization**
**Duration:** 60 minutes  
**Objective:** Set up your development environment and containerize the Flask application

- Exercise 1: Install and configure required tools
- Exercise 2: Set up AWS credentials and GitHub repository
- Exercise 3: Create Docker configuration files
- Exercise 4: Build and test containerized application
- Exercise 5: Implement health checks and optimization

### **Lab 02: Infrastructure Foundation with Terraform**
**Duration:** 90 minutes  
**Objective:** Create reusable infrastructure modules and deploy networking foundation

- Exercise 1: Design Terraform module architecture
- Exercise 2: Create VPC and networking components
- Exercise 3: Implement security groups and access control
- Exercise 4: Deploy and validate infrastructure
- Exercise 5: Create environment-specific configurations

### **Lab 03: Database Infrastructure and Management**
**Duration:** 45 minutes  
**Objective:** Deploy and configure PostgreSQL database with proper security

- Exercise 1: Create RDS module with best practices
- Exercise 2: Configure database security and networking
- Exercise 3: Implement backup and monitoring
- Exercise 4: Test database connectivity and performance
- Exercise 5: Create database initialization scripts

### **Lab 04: Compute Infrastructure and Load Balancing**
**Duration:** 75 minutes  
**Objective:** Deploy EC2 instances with auto-scaling and load balancing

- Exercise 1: Create Application Load Balancer configuration
- Exercise 2: Design EC2 launch templates and auto-scaling
- Exercise 3: Implement health checks and monitoring
- Exercise 4: Configure user data and application deployment
- Exercise 5: Test load balancing and scaling behavior

### **Lab 05: CI/CD Pipeline Implementation**
**Duration:** 90 minutes  
**Objective:** Implement automated testing, building, and deployment pipeline

- Exercise 1: Set up GitHub Actions workflow structure
- Exercise 2: Create automated testing and security scanning
- Exercise 3: Configure Docker image building and ECR integration
- Exercise 4: Implement multi-environment deployment strategy
- Exercise 5: Test complete CI/CD pipeline

### **Lab 06: Monitoring, Logging, and Alerting**
**Duration:** 60 minutes  
**Objective:** Implement comprehensive monitoring and alerting system

- Exercise 1: Configure CloudWatch metrics and alarms
- Exercise 2: Set up centralized logging
- Exercise 3: Create monitoring dashboards
- Exercise 4: Implement alert notifications
- Exercise 5: Test monitoring and alerting scenarios

### **Lab 07: Multi-Environment Deployment and Management**
**Duration:** 45 minutes  
**Objective:** Deploy and manage multiple environments (dev, staging, production)

- Exercise 1: Create environment-specific configurations
- Exercise 2: Deploy staging and production environments
- Exercise 3: Implement environment promotion workflows
- Exercise 4: Test cross-environment functionality
- Exercise 5: Implement rollback procedures

## Getting Started

1. **Clone or download this repository**
2. **Read the prerequisites** and ensure your environment is ready
3. **Start with Lab 01** and follow the exercises in order
4. **Complete each exercise** before moving to the next
5. **Use the verification steps** to ensure each exercise is completed successfully

## Lab Format

Each lab follows a consistent structure:
- **Overview and Objectives** - What you'll accomplish
- **Prerequisites** - What you need before starting
- **Exercises** - Step-by-step instructions with verification
- **Summary** - What you've accomplished and next steps
- **Troubleshooting** - Common issues and solutions

## Support and Resources

- **Common Issues**: Check the troubleshooting section in each lab
- **Additional Resources**: Links to documentation and best practices
- **Community**: Consider contributing improvements via pull requests

## Estimated Total Time

**Complete all labs: 6-8 hours**
- Can be completed over multiple sessions
- Each lab builds on the previous one
- Checkpoints allow for stopping and resuming

---

**Ready to get started?** Begin with [Lab 01: Environment Setup and Application Containerization](./01-environment-setup-containerization.md)