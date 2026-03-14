#!/bin/bash
# ============================================================================
# Voice Agent - WSL Ubuntu Setup Script
# Automated installation and configuration for WSL2
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# ============================================================================
# System Check
# ============================================================================

check_wsl() {
    print_header "WSL System Check"
    
    if grep -qi microsoft /proc/version; then
        print_success "Running on WSL2"
    else
        print_error "Not running on WSL2. Please use WSL2 for this setup."
        exit 1
    fi
    
    # Check Ubuntu version
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        print_success "Detected: $PRETTY_NAME"
    fi
}

# ============================================================================
# Install Dependencies
# ============================================================================

install_system_packages() {
    print_header "Installing System Dependencies"
    
    print_warning "Updating package lists (may take a minute)..."
    sudo apt-get update -qq
    
    # Essential packages
    PACKAGES=(
        "curl"
        "wget"
        "git"
        "build-essential"
        "python3-dev"
        "python3-pip"
        "python3-venv"
        "supervisor"
        "ca-certificates"
        "gnupg"
        "lsb-release"
        "apt-transport-https"
        "net-tools"
        "iputils-ping"
        "jq"
    )
    
    for package in "${PACKAGES[@]}"; do
        if sudo apt-get install -y -qq "$package" 2>/dev/null; then
            print_success "Installed: $package"
        fi
    done
}

install_docker() {
    print_header "Installing Docker"
    
    # Check if docker is already installed
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version)
        print_success "Docker already installed: $DOCKER_VERSION"
        return 0
    fi
    
    print_warning "Installing Docker..."
    
    # Install Docker
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg 2>/dev/null
    
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    sudo apt-get update -qq
    sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin 2>/dev/null
    
    # Enable Docker service
    sudo usermod -aG docker "$USER" 2>/dev/null || true
    
    print_success "Docker installed: $(docker --version)"
}

install_docker_compose() {
    print_header "Installing Docker Compose"
    
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version)
        print_success "Docker Compose already installed: $COMPOSE_VERSION"
        return 0
    fi
    
    print_warning "Installing Docker Compose..."
    
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose 2>/dev/null
    sudo chmod +x /usr/local/bin/docker-compose
    
    print_success "Docker Compose installed: $(docker-compose --version)"
}

# ============================================================================
# WSL Optimizations
# ============================================================================

setup_wsl_optimizations() {
    print_header "WSL Optimizations"
    
    print_warning "Note: For optimal performance, add these to your %USERPROFILE%\.wslconfig (Windows file):"
    echo ""
    echo "[wsl2]"
    echo "memory=8GB"
    echo "processors=4"
    echo "swap=4GB"
    echo "localhostForwarding=true"
    echo ""
    print_warning "Then restart WSL with: wsl --shutdown"
}

# ============================================================================
# Project Setup
# ============================================================================

setup_project() {
    print_header "Setting Up Voice Agent Project"
    
    cd "$PROJECT_ROOT"
    
    # Create directories if needed
    mkdir -p logs data models cache
    print_success "Created project directories"
    
    # Check if .env exists
    if [ ! -f ".env" ]; then
        print_warning ".env file not found, creating from template..."
        touch .env
        cat > .env << 'EOF'
ENVIRONMENT=development
DEBUG=true
DB_HOST=postgres
DB_NAME=voice_agent
DB_USER=postgres
DB_PASSWORD=postgres
REDIS_HOST=redis
REDIS_PORT=6379
FREESWITCH_HOST=freeswitch
FREESWITCH_PORT=8021
FREESWITCH_PASSWORD=ClueCon
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
STT_MODEL=base
AUDIO_SAMPLE_RATE=16000
EOF
        print_success "Created .env file"
    else
        print_success ".env file already exists"
    fi
    
    # Create docker network (optional, docker-compose does this)
    # docker network create voice-network 2>/dev/null || true
    
    print_success "Project setup complete"
}

# ============================================================================
# Docker Setup for WSL
# ============================================================================

start_docker_service() {
    print_header "Starting Docker Service"
    
    # Check if Docker daemon is running
    if docker ps &>/dev/null; then
        print_success "Docker service is running"
        return 0
    fi
    
    print_warning "Docker service not running, attempting to start..."
    
    # Try to start Docker service
    if sudo service docker start 2>/dev/null; then
        sleep 2
        if docker ps &>/dev/null; then
            print_success "Docker service started successfully"
            return 0
        fi
    fi
    
    # If service start failed, try systemctl
    if sudo systemctl start docker 2>/dev/null; then
        sleep 2
        if docker ps &>/dev/null; then
            print_success "Docker service started successfully"
            return 0
        fi
    fi
    
    print_error "Failed to start Docker service"
    print_warning "Try starting Docker Desktop from Windows or run: sudo dockerd"
    return 1
}

# ============================================================================
# Build & Launch Services
# ============================================================================

build_services() {
    print_header "Building Docker Images"
    
    cd "$PROJECT_ROOT"
    
    print_warning "Building images (this may take 10-15 minutes on first run)..."
    
    if docker-compose build 2>&1 | tee build.log; then
        print_success "Docker images built successfully"
        return 0
    else
        print_error "Docker build failed. Check build.log for details"
        return 1
    fi
}

start_services() {
    print_header "Starting Services"
    
    cd "$PROJECT_ROOT"
    
    print_warning "Starting all services..."
    
    # Start services in background
    docker-compose up -d
    
    print_success "Services starting..."
    print_warning "Waiting for services to be ready (this may take 30-60 seconds)..."
    
    sleep 20
    
    # Check service status
    echo ""
    print_header "Service Status"
    docker-compose ps
}

# ============================================================================
# Verification
# ============================================================================

verify_services() {
    print_header "Verifying Services"
    
    # Count healthy services
    HEALTHY=0
    TOTAL=0
    
    # Check FastAPI
    if curl -s http://localhost:8000/health &>/dev/null; then
        print_success "FastAPI Gateway is healthy"
        ((HEALTHY++))
    else
        print_warning "FastAPI Gateway is starting..."
    fi
    ((TOTAL++))
    
    # Check PostgreSQL
    if docker-compose exec -T postgres pg_isready -U postgres &>/dev/null 2>&1; then
        print_success "PostgreSQL is ready"
        ((HEALTHY++))
    else
        print_warning "PostgreSQL is starting..."
    fi
    ((TOTAL++))
    
    # Check Redis
    if docker-compose exec -T redis redis-cli ping &>/dev/null 2>&1 | grep -q "PONG"; then
        print_success "Redis is ready"
        ((HEALTHY++))
    else
        print_warning "Redis is starting..."
    fi
    ((TOTAL++))
    
    echo ""
    print_success "$HEALTHY/$TOTAL services ready"
    
    if [ $HEALTHY -lt $TOTAL ]; then
        print_warning "Some services are still starting. Check logs with: docker-compose logs -f"
    fi
}

# ============================================================================
# Access Information
# ============================================================================

show_access_info() {
    print_header "Access Information"
    
    echo ""
    echo -e "${GREEN}Web Services:${NC}"
    echo "  FastAPI API:      http://localhost:8000"
    echo "  API Docs:         http://localhost:8000/docs"
    echo "  Grafana:          http://localhost:3000 (admin/admin)"
    echo "  Jaeger:           http://localhost:16686"
    echo "  Prometheus:       http://localhost:9090"
    echo "  Kibana:           http://localhost:5601"
    echo ""
    echo -e "${GREEN}Database:${NC}"
    echo "  PostgreSQL:       localhost:5432"
    echo "  User:             postgres"
    echo "  Database:         voice_agent"
    echo ""
    echo -e "${GREEN}Cache & Messaging:${NC}"
    echo "  Redis:            localhost:6379"
    echo "  Kafka:            localhost:9092"
    echo ""
    echo -e "${GREEN}SIP Services:${NC}"
    echo "  FreeSWITCH ESL:   localhost:8021"
    echo "  Kamailio SIP:     localhost:5061"
    echo ""
    echo -e "${GREEN}Useful Commands:${NC}"
    echo "  View logs:        docker-compose logs -f <service>"
    echo "  Stop services:    docker-compose down"
    echo "  Restart:          docker-compose restart"
    echo "  Clean rebuild:    docker-compose down -v && docker-compose build --no-cache"
    echo ""
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    print_header "🎤 Voice Agent - WSL Ubuntu Setup"
    
    # Run checks and installations
    check_wsl
    install_system_packages
    install_docker
    install_docker_compose
    setup_wsl_optimizations
    setup_project
    
    # Start services
    if ! start_docker_service; then
        print_error "Docker service is not running. Please start Docker Desktop or docker daemon."
        exit 1
    fi
    
    if ! build_services; then
        print_error "Failed to build services"
        exit 1
    fi
    
    start_services
    sleep 10
    verify_services
    show_access_info
    
    print_header "✅ Setup Complete!"
    echo ""
    print_success "Voice Agent project is ready on WSL Ubuntu!"
    echo ""
    print_warning "Next steps:"
    echo "  1. Wait a few minutes for all services to fully start"
    echo "  2. Visit http://localhost:8000/health to check API status"
    echo "  3. Access Grafana dashboard at http://localhost:3000"
    echo "  4. Check logs: docker-compose logs -f"
    echo ""
}

# Run main function
main "$@"
