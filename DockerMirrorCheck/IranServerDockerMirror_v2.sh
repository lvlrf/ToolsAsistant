#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# IranServerDockerMirror v2.0 - Enhanced Edition
# ============================================================================
# Features:
# - Parallel mirror testing for 5x faster execution
# - Enhanced error handling & logging
# - Extended timeout for weak connections
# - More Iranian mirrors
# - Automatic cleanup & retry mechanism
# - Root privilege check
# - Colored output
# ============================================================================

# ------------------ Configuration ------------------
readonly SCRIPT_VERSION="2.0"
readonly LOG_FILE="/var/log/docker-mirror-setup.log"
readonly DAEMON_JSON="/etc/docker/daemon.json"
readonly MAX_WORKERS=10  # Parallel testing workers
readonly V2_TIMEOUT=6    # Increased from 4s
readonly MANIFEST_TIMEOUT=10  # Increased from 7s
readonly DOCKER_RESTART_RETRIES=3

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# ------------------ Mirror Candidates ------------------
CANDIDATES=(
  # Primary Iranian mirrors (most reliable)
  "https://focker.ir"
  "https://docker.arvancloud.ir"
  "https://registry.docker.ir"
  "https://hub.hamdocker.ir"
  
  # Secondary Iranian mirrors
  "https://docker.mobinhost.com"
  "https://docker.manageit.ir"
  "https://docker.iranrepo.ir"
  "https://mirror.amin.ac.ir"
  
  # Chinese mirrors (fallback)
  "https://docker.m.daocloud.io"
  "https://dockerproxy.com"
  "https://hub-mirror.c.163.com"
  "https://mirror.ccs.tencentyun.com"
  "https://dockerhub.azk8s.cn"
  "https://registry.docker-cn.com"
  
  # Global fallbacks
  "https://mirror.gcr.io"
  "https://registry-1.docker.io"
)

# ------------------ Helper Functions ------------------
log() {
  local level="$1"
  shift
  local msg="$*"
  local timestamp
  timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
  echo -e "${timestamp} [${level}] ${msg}" | tee -a "$LOG_FILE"
}

log_info() { echo -e "${BLUE}ℹ${NC} $*"; log "INFO" "$*"; }
log_success() { echo -e "${GREEN}✓${NC} $*"; log "SUCCESS" "$*"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $*"; log "WARNING" "$*"; }
log_error() { echo -e "${RED}✗${NC} $*" >&2; log "ERROR" "$*"; }

print_header() {
  echo -e "\n${CYAN}═══════════════════════════════════════════════════${NC}"
  echo -e "${CYAN}  $*${NC}"
  echo -e "${CYAN}═══════════════════════════════════════════════════${NC}\n"
}

cleanup() {
  rm -f /tmp/docker-mirror-*.tmp 2>/dev/null || true
}

trap cleanup EXIT

# ------------------ Dependency Checks ------------------
check_root() {
  if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
  fi
}

check_dependencies() {
  local missing=()
  
  command -v curl >/dev/null 2>&1 || missing+=("curl")
  command -v docker >/dev/null 2>&1 || missing+=("docker")
  
  if [[ ${#missing[@]} -gt 0 ]]; then
    log_error "Missing required commands: ${missing[*]}"
    exit 1
  fi
  
  # Auto-install jq if missing
  if ! command -v jq >/dev/null 2>&1; then
    log_info "Installing jq..."
    apt-get update -qq >/dev/null 2>&1
    apt-get install -y jq >/dev/null 2>&1
  fi
  
  # Check Docker version
  local docker_version
  docker_version="$(docker --version | grep -oP '\d+\.\d+' | head -1)"
  log_info "Docker version: $docker_version"
}

# ------------------ Mirror Testing Functions ------------------
# Test /v2 endpoint (parallel-safe)
check_v2() {
  local base="${1%/}"
  local code
  code="$(curl -sS -L --max-time "$V2_TIMEOUT" \
    -o /dev/null -w "%{http_code}" \
    "$base/v2/" 2>/dev/null || echo "000")"
  
  if [[ "$code" == "200" || "$code" == "401" ]]; then
    echo "$base"
    return 0
  fi
  return 1
}

# Test manifest + measure latency (parallel-safe)
check_manifest() {
  local base="${1%/}"
  local code time_total
  
  read -r code time_total < <(
    curl -sS -I -L --max-time "$MANIFEST_TIMEOUT" \
      -o /dev/null -w "%{http_code} %{time_total}" \
      -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
      "$base/v2/library/hello-world/manifests/latest" 2>/dev/null \
    || echo "000 999"
  )
  
  # Reject 403 (blocked), 404 (not found), 000 (timeout/error)
  if [[ "$code" == "403" || "$code" == "404" || "$code" == "000" ]]; then
    return 1
  fi
  
  # Output: latency mirror_url http_code
  printf "%s %s %s\n" "$time_total" "$base" "$code"
}

# Parallel testing wrapper
test_mirrors_parallel() {
  local -n mirrors_ref=$1
  local test_func=$2
  local tmp_results="/tmp/docker-mirror-$$.tmp"
  
  > "$tmp_results"  # Clear file
  
  # Use background jobs with limited workers
  local active_jobs=0
  for mirror in "${mirrors_ref[@]}"; do
    # Wait if too many jobs
    while [[ $active_jobs -ge $MAX_WORKERS ]]; do
      wait -n 2>/dev/null || true
      ((active_jobs--)) || true
    done
    
    # Start background job
    {
      if result=$($test_func "$mirror" 2>/dev/null); then
        echo "$result" >> "$tmp_results"
      fi
    } &
    
    ((active_jobs++)) || true
  done
  
  # Wait for all remaining jobs
  wait
  
  # Read results
  if [[ -s "$tmp_results" ]]; then
    cat "$tmp_results"
    return 0
  fi
  return 1
}

# ------------------ Main Mirror Selection ------------------
select_best_mirrors() {
  print_header "Phase 1: Testing Mirror Availability (${#CANDIDATES[@]} candidates)"
  
  local alive_file="/tmp/docker-mirror-alive-$$.tmp"
  
  log_info "Testing /v2 endpoints in parallel..."
  if ! test_mirrors_parallel CANDIDATES check_v2 > "$alive_file"; then
    log_error "No mirrors passed /v2 check"
    return 1
  fi
  
  mapfile -t alive < "$alive_file"
  log_success "Found ${#alive[@]} alive mirrors"
  printf "${GREEN}  ✓${NC} %s\n" "${alive[@]}"
  
  if [[ ${#alive[@]} -eq 0 ]]; then
    return 1
  fi
  
  # ------------------ Phase 2: Latency Test ------------------
  print_header "Phase 2: Testing Manifest Speed & Accessibility"
  
  local manifest_file="/tmp/docker-mirror-manifest-$$.tmp"
  
  log_info "Testing manifest endpoints in parallel..."
  if ! test_mirrors_parallel alive check_manifest > "$manifest_file"; then
    log_error "No mirrors passed manifest check"
    return 1
  fi
  
  # Sort by latency (first column)
  local ranked
  ranked="$(sort -n "$manifest_file")"
  
  echo -e "\n${CYAN}Ranked Results (latency in seconds):${NC}"
  echo "$ranked" | while read -r latency mirror code; do
    printf "  ${GREEN}%.3fs${NC} - %s ${YELLOW}(HTTP %s)${NC}\n" "$latency" "$mirror" "$code"
  done
  
  # Select top 2
  local m1 m2
  m1="$(echo "$ranked" | awk 'NR==1{print $2}')"
  m2="$(echo "$ranked" | awk 'NR==2{print $2}')"
  
  SELECTED_MIRRORS=("$m1")
  [[ -n "${m2:-}" ]] && SELECTED_MIRRORS+=("$m2")
  
  echo -e "\n${GREEN}✓ Selected Mirrors:${NC}"
  printf "  ${CYAN}[%d]${NC} %s\n" {1..${#SELECTED_MIRRORS[@]}} "${SELECTED_MIRRORS[@]}"
  
  return 0
}

# ------------------ Docker Configuration ------------------
update_docker_config() {
  print_header "Phase 3: Updating Docker Configuration"
  
  mkdir -p "$(dirname "$DAEMON_JSON")"
  
  # Backup existing config
  if [[ -f "$DAEMON_JSON" ]]; then
    local backup_file="${DAEMON_JSON}.backup.$(date +%Y%m%d_%H%M%S)"
    cp -a "$DAEMON_JSON" "$backup_file"
    log_success "Backup created: $backup_file"
  fi
  
  # Build mirrors JSON array
  local mirrors_json
  mirrors_json="$(printf "%s\n" "${SELECTED_MIRRORS[@]}" | jq -R . | jq -s .)"
  
  # Read existing config or use empty object
  local existing_json="{}"
  if [[ -s "$DAEMON_JSON" ]]; then
    existing_json="$(cat "$DAEMON_JSON")"
  fi
  
  # Merge: update only registry-mirrors, keep everything else
  local merged
  merged="$(jq --argjson mirrors "$mirrors_json" '
    if type != "object" then {} else . end
    | .["registry-mirrors"] = $mirrors
  ' <<<"$existing_json")"
  
  # Write and validate
  echo "$merged" > "$DAEMON_JSON"
  
  if ! jq . "$DAEMON_JSON" >/dev/null 2>&1; then
    log_error "Generated invalid JSON! Restoring backup..."
    [[ -f "$backup_file" ]] && cp "$backup_file" "$DAEMON_JSON"
    return 1
  fi
  
  log_success "Configuration updated successfully"
  echo -e "\n${CYAN}Current daemon.json:${NC}"
  jq . "$DAEMON_JSON"
}

# ------------------ Docker Service Restart ------------------
restart_docker() {
  print_header "Phase 4: Restarting Docker Service"
  
  local retry=0
  while [[ $retry -lt $DOCKER_RESTART_RETRIES ]]; do
    if [[ $retry -gt 0 ]]; then
      log_warning "Retry attempt $retry/$DOCKER_RESTART_RETRIES..."
      sleep 2
    fi
    
    # Reset failed state
    systemctl reset-failed docker docker.socket >/dev/null 2>&1 || true
    
    # Restart
    if systemctl restart docker 2>/dev/null; then
      sleep 3
      
      # Verify Docker is running
      if systemctl is-active docker >/dev/null 2>&1; then
        log_success "Docker service restarted successfully"
        
        # Show active mirrors
        echo -e "\n${CYAN}Active Registry Mirrors:${NC}"
        docker info 2>/dev/null | grep -A 10 "Registry Mirrors:" || true
        
        return 0
      fi
    fi
    
    ((retry++)) || true
  done
  
  log_error "Failed to restart Docker after $DOCKER_RESTART_RETRIES attempts"
  return 1
}

# ------------------ Pull Test ------------------
test_pull() {
  print_header "Phase 5: Verification Test"
  
  log_info "Removing existing hello-world image..."
  docker image rm -f hello-world:latest >/dev/null 2>&1 || true
  
  log_info "Pulling hello-world (forced network pull)..."
  
  local start_time
  start_time="$(date +%s)"
  
  if docker pull hello-world:latest 2>&1 | tee -a "$LOG_FILE"; then
    local end_time duration
    end_time="$(date +%s)"
    duration=$((end_time - start_time))
    
    log_success "Pull completed in ${duration}s"
    
    if docker run --rm hello-world >/dev/null 2>&1; then
      log_success "Container test passed"
      return 0
    else
      log_error "Container failed to run"
      return 1
    fi
  else
    log_error "Pull failed"
    return 1
  fi
}

# ------------------ Main Execution ------------------
main() {
  echo -e "${CYAN}"
  cat << "EOF"
╔════════════════════════════════════════════════════════════╗
║     IranServerDockerMirror v2.0 - Enhanced Edition         ║
║     Automatic Docker Registry Mirror Optimizer             ║
╚════════════════════════════════════════════════════════════╝
EOF
  echo -e "${NC}"
  
  log_info "Script started at $(date)"
  log_info "Log file: $LOG_FILE"
  
  # Pre-flight checks
  check_root
  check_dependencies
  
  # Main workflow
  if ! select_best_mirrors; then
    log_error "Failed to find suitable mirrors"
    exit 1
  fi
  
  if ! update_docker_config; then
    log_error "Failed to update Docker configuration"
    exit 1
  fi
  
  if ! restart_docker; then
    log_error "Failed to restart Docker service"
    exit 1
  fi
  
  if ! test_pull; then
    log_warning "Pull test failed, but configuration was updated"
    exit 1
  fi
  
  # Success summary
  print_header "✓ Setup Complete"
  echo -e "${GREEN}Selected Mirrors:${NC}"
  printf "  • %s\n" "${SELECTED_MIRRORS[@]}"
  echo
  log_success "All operations completed successfully!"
  log_info "You can now use: docker pull <image>"
}

# Run main function
main "$@"
