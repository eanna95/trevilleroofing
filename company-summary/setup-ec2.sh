#!/bin/bash

# EC2 Setup Script for Company Summary Docker Deployment
# This script installs Docker, Docker Compose, and other dependencies
# Compatible with Amazon Linux 2, Ubuntu, and CentOS/RHEL

set -e  # Exit on any error

echo "🚀 Starting EC2 setup for Company Summary deployment..."

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    echo "📋 Detected OS: $OS"
else
    echo "❌ Cannot detect OS. This script supports Amazon Linux 2, Ubuntu, and CentOS/RHEL."
    exit 1
fi

# Update system packages
echo "📦 Updating system packages..."
case "$OS" in
    *"Amazon Linux"*|*"CentOS"*|*"Red Hat"*)
        sudo yum update -y
        sudo yum install -y curl wget git unzip
        ;;
    *"Ubuntu"*|*"Debian"*)
        sudo apt-get update
        sudo apt-get install -y curl wget git unzip
        ;;
    *)
        echo "❌ Unsupported OS: $OS"
        exit 1
        ;;
esac

# Install Docker
echo "🐳 Installing Docker..."
case "$OS" in
    *"Amazon Linux"*)
        # Amazon Linux 2
        sudo yum install -y docker
        sudo systemctl start docker
        sudo systemctl enable docker
        ;;
    *"Ubuntu"*|*"Debian"*)
        # Ubuntu/Debian
        sudo apt-get install -y apt-transport-https ca-certificates gnupg lsb-release
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io
        sudo systemctl start docker
        sudo systemctl enable docker
        ;;
    *"CentOS"*|*"Red Hat"*)
        # CentOS/RHEL
        sudo yum install -y yum-utils
        sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        sudo yum install -y docker-ce docker-ce-cli containerd.io
        sudo systemctl start docker
        sudo systemctl enable docker
        ;;
esac

# Install Docker Compose
echo "🐙 Installing Docker Compose..."
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add current user to docker group
echo "👥 Adding current user to docker group..."
sudo usermod -aG docker $USER

# Install additional useful tools
echo "🛠️  Installing additional tools..."
case "$OS" in
    *"Amazon Linux"*|*"CentOS"*|*"Red Hat"*)
        sudo yum install -y htop nano vim tree
        ;;
    *"Ubuntu"*|*"Debian"*)
        sudo apt-get install -y htop nano vim tree
        ;;
esac

# Create deployment directory
echo "📁 Creating deployment directory..."
mkdir -p ~/company-summary-deployment
cd ~/company-summary-deployment

# Configure firewall (if ufw is available)
if command -v ufw &> /dev/null; then
    echo "🔒 Configuring firewall..."
    sudo ufw allow 22/tcp
    sudo ufw allow 3000/tcp
    echo "y" | sudo ufw enable
fi

# Display versions
echo ""
echo "✅ Installation complete! Here are the installed versions:"
echo "📊 System Info:"
echo "   OS: $OS"
echo "   User: $USER"
echo ""
echo "🐳 Docker: $(docker --version)"
echo "🐙 Docker Compose: $(docker-compose --version)"
echo ""
echo "📁 Deployment directory created at: ~/company-summary-deployment"
echo ""
echo "⚠️  IMPORTANT: You need to log out and log back in (or run 'newgrp docker')"
echo "   for docker group membership to take effect."
echo ""
echo "🚀 Next steps:"
echo "   1. Log out and log back in"
echo "   2. Upload your company-summary files to ~/company-summary-deployment/"
echo "   3. Run: cd ~/company-summary-deployment && docker-compose up -d"
echo "   4. Access your app at: http://your-ec2-public-ip:3000"
echo ""
echo "🔧 To test Docker without logging out, run: newgrp docker"