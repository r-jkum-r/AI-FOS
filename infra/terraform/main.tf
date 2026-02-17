# Terraform configuration for AWS deployment
# This automates the EC2 instance creation

terraform {
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

# Variables
variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  default     = "t3.xlarge"
}

variable "key_name" {
  description = "SSH key pair name"
  type        = string
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH"
  default     = "0.0.0.0/0"  # Change to your IP for security
}

# Get latest Ubuntu AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

# Security Group
resource "aws_security_group" "voice_agent" {
  name        = "voice-agent-sg"
  description = "Security group for AI Voice Agent"

  # SSH
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
    description = "SSH access"
  }

  # API
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "API access"
  }

  # SIP UDP
  ingress {
    from_port   = 5060
    to_port     = 5060
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SIP signaling UDP"
  }

  # SIP TCP
  ingress {
    from_port   = 5060
    to_port     = 5060
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SIP signaling TCP"
  }

  # RTP
  ingress {
    from_port   = 10000
    to_port     = 10100
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "RTP audio"
  }

  # Grafana
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
    description = "Grafana dashboard"
  }

  # Prometheus
  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
    description = "Prometheus"
  }

  # Outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }

  tags = {
    Name = "voice-agent-sg"
  }
}

# EC2 Instance
resource "aws_instance" "voice_agent" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  key_name      = var.key_name

  vpc_security_group_ids = [aws_security_group.voice_agent.id]

  root_block_device {
    volume_size = 100
    volume_type = "gp3"
  }

  user_data = <<-EOF
              #!/bin/bash
              apt-get update
              apt-get install -y docker.io docker-compose git
              usermod -aG docker ubuntu
              
              # Clone and setup (replace with your repo)
              cd /home/ubuntu
              # git clone <your-repo-url> voice-ai-agent
              # chown -R ubuntu:ubuntu voice-ai-agent
              EOF

  tags = {
    Name = "voice-agent-server"
  }
}

# Elastic IP
resource "aws_eip" "voice_agent" {
  instance = aws_instance.voice_agent.id
  domain   = "vpc"

  tags = {
    Name = "voice-agent-eip"
  }
}

# Outputs
output "instance_id" {
  value = aws_instance.voice_agent.id
}

output "public_ip" {
  value = aws_eip.voice_agent.public_ip
}

output "ssh_command" {
  value = "ssh -i ${var.key_name}.pem ubuntu@${aws_eip.voice_agent.public_ip}"
}

output "api_url" {
  value = "http://${aws_eip.voice_agent.public_ip}:8000"
}

output "grafana_url" {
  value = "http://${aws_eip.voice_agent.public_ip}:3000"
}
