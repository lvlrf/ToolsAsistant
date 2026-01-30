#!/bin/bash
#
# Fastly CDN IP Scanner - Bash Wrapper
# Version: 1.0
# Developed by: DrConnect
# Channel: https://t.me/drconnect
#
# Description:
# Bash wrapper to check dependencies and run the Python scanner
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCANNER_PY="${SCRIPT_DIR}/scanner.py"

# ==================== FUNCTIONS ====================

print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║        Fastly CDN IP Scanner v1.0                  ║${NC}"
    echo -e "${BLUE}║        Developed by: DrConnect                     ║${NC}"
    echo -e "${BLUE}║        Channel: https://t.me/drconnect            ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            OS=$NAME
            VER=$VERSION_ID
        else
            OS="Linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macOS"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        OS="Windows"
    else
        OS="Unknown"
    fi
    
    print_info "Detected OS: $OS"
}

# Check Python3
check_python() {
    print_info "Checking for Python3..."
    
    if command_exists python3; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        print_success "Python3 found: $PYTHON_VERSION"
        return 0
    elif command_exists python; then
        # Check if 'python' is Python 3
        if python --version 2>&1 | grep -q "Python 3"; then
            PYTHON_CMD="python"
            PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
            print_success "Python3 found: $PYTHON_VERSION"
            return 0
        fi
    fi
    
    return 1
}

# Check pip
check_pip() {
    print_info "Checking for pip..."
    
    if command_exists pip3; then
        PIP_CMD="pip3"
        print_success "pip3 found"
        return 0
    elif command_exists pip; then
        PIP_CMD="pip"
        print_success "pip found"
        return 0
    elif $PYTHON_CMD -m pip --version >/dev/null 2>&1; then
        PIP_CMD="$PYTHON_CMD -m pip"
        print_success "pip module found"
        return 0
    fi
    
    return 1
}

# Check required Python packages
check_packages() {
    print_info "Checking required Python packages..."
    
    local packages=("requests" "tqdm")
    local missing=()
    
    for package in "${packages[@]}"; do
        if ! $PYTHON_CMD -c "import $package" 2>/dev/null; then
            missing+=("$package")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        print_error "Missing packages: ${missing[*]}"
        print_info "Please install with: $PIP_CMD install ${missing[*]}"
        return 1
    else
        print_success "All required packages are installed"
        return 0
    fi
}

# Check if scanner.py exists
check_scanner_py() {
    if [ ! -f "$SCANNER_PY" ]; then
        print_error "scanner.py not found!"
        print_info "Expected location: $SCANNER_PY"
        print_info "Please ensure scanner.py is in the same directory as this script"
        exit 1
    fi
    print_success "scanner.py found"
}

# Make scanner.py executable
make_executable() {
    if [ ! -x "$SCANNER_PY" ]; then
        chmod +x "$SCANNER_PY"
        print_info "Made scanner.py executable"
    fi
}

# Run the scanner
run_scanner() {
    print_info "Starting Fastly CDN IP Scanner..."
    echo ""
    
    # Run with Python
    $PYTHON_CMD "$SCANNER_PY" "$@"
}

# Cleanup on exit
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo ""
        print_error "Scanner exited with code: $exit_code"
    fi
    exit $exit_code
}

trap cleanup EXIT

# ==================== MAIN ====================

main() {
    clear
    print_header
    
    # Detect OS
    detect_os
    echo ""
    
    # Check Python3
    if ! check_python; then
        print_error "Python3 is required but not found"
        print_info "Please install Python3:"
        
        if [[ "$OS" == *"Ubuntu"* || "$OS" == *"Debian"* ]]; then
            print_info "  sudo apt-get install python3 python3-pip"
        elif [[ "$OS" == *"CentOS"* || "$OS" == *"Red Hat"* || "$OS" == *"Fedora"* ]]; then
            print_info "  sudo yum install python3 python3-pip"
        elif [[ "$OS" == *"macOS"* ]]; then
            print_info "  brew install python3"
        else
            print_info "  Visit: https://www.python.org/downloads/"
        fi
        
        exit 1
    fi
    
    # Check pip
    if ! check_pip; then
        print_error "pip is required but not found"
        print_info "Please install pip:"
        
        if [[ "$OS" == *"Ubuntu"* || "$OS" == *"Debian"* ]]; then
            print_info "  sudo apt-get install python3-pip"
        elif [[ "$OS" == *"CentOS"* || "$OS" == *"Red Hat"* || "$OS" == *"Fedora"* ]]; then
            print_info "  sudo yum install python3-pip"
        else
            print_info "  Visit: https://pip.pypa.io/en/stable/installation/"
        fi
        
        exit 1
    fi
    
    # Check packages
    if ! check_packages; then
        exit 1
    fi
    
    echo ""
    
    # Check scanner.py
    check_scanner_py
    
    # Make executable
    make_executable
    
    echo ""
    print_success "All dependencies satisfied"
    echo ""
    echo "Press Enter to start the scanner..."
    read -r
    
    # Run scanner
    run_scanner "$@"
}

# ==================== ENTRY POINT ====================

# Check if running with sudo (not recommended)
if [ "$EUID" -eq 0 ]; then 
    print_warning "Running as root is not recommended"
    print_info "The scanner does not require root privileges"
    echo ""
fi

# Run main function
main "$@"

