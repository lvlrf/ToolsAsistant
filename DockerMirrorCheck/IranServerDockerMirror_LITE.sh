#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# IranServerDockerMirror LITE v2.0
# ============================================================================
# Optimized for: Very weak networks, low resources
# Features: Minimal overhead, longer timeouts, sequential testing
# Use when: Standard version times out or fails
# ============================================================================

# ------------------ Configuration ------------------
readonly V2_TIMEOUT=15      # Extra long for weak connections
readonly MANIFEST_TIMEOUT=20
readonly DOCKER_RESTART_RETRIES=5

# Iranian mirrors only (most reliable in Iran)
MIRRORS=(
  "https://focker.ir"
  "https://docker.arvancloud.ir"
  "https://registry.docker.ir"
  "https://hub.hamdocker.ir"
  "https://docker.iranrepo.ir"
)

# ------------------ Simple Functions ------------------
log() { echo "[$(date '+%H:%M:%S')] $*"; }
die() { log "ERROR: $*" >&2; exit 1; }

# Check /v2
test_v2() {
  local url="${1%/}"
  local code
  code=$(curl -sS -L --max-time "$V2_TIMEOUT" -o /dev/null -w "%{http_code}" "$url/v2/" 2>/dev/null || echo "000")
  [[ "$code" == "200" || "$code" == "401" ]]
}

# Measure latency
test_speed() {
  local url="${1%/}"
  local latency
  latency=$(curl -sS -I -L --max-time "$MANIFEST_TIMEOUT" -o /dev/null -w "%{time_total}" \
    -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
    "$url/v2/library/hello-world/manifests/latest" 2>/dev/null || echo "999")
  echo "$latency $url"
}

# ------------------ Main ------------------
main() {
  log "Starting Docker Mirror Setup (LITE version)"
  
  # Check root
  [[ $EUID -eq 0 ]] || die "Must run as root (use sudo)"
  
  # Check Docker
  command -v docker >/dev/null || die "Docker not found"
  
  # Install jq if needed
  if ! command -v jq >/dev/null; then
    log "Installing jq..."
    apt-get update -qq && apt-get install -y jq -qq
  fi
  
  # Test mirrors (sequential for stability)
  log "Testing ${#MIRRORS[@]} mirrors (this may take 1-2 minutes)..."
  
  working=()
  for mirror in "${MIRRORS[@]}"; do
    if test_v2 "$mirror"; then
      log "✓ $mirror"
      working+=("$mirror")
    else
      log "✗ $mirror"
    fi
  done
  
  [[ ${#working[@]} -eq 0 ]] && die "No working mirrors found"
  
  log "Found ${#working[@]} working mirror(s)"
  
  # Measure speed
  log "Measuring speed..."
  results=$(mktemp)
  for mirror in "${working[@]}"; do
    test_speed "$mirror" >> "$results"
  done
  
  # Select best 2
  sorted=$(sort -n "$results")
  m1=$(echo "$sorted" | awk 'NR==1{print $2}')
  m2=$(echo "$sorted" | awk 'NR==2{print $2}')
  
  selected=("$m1")
  [[ -n "$m2" ]] && selected+=("$m2")
  
  log "Selected: ${selected[*]}"
  
  # Update config
  log "Updating Docker configuration..."
  
  mkdir -p /etc/docker
  
  # Backup
  if [[ -f /etc/docker/daemon.json ]]; then
    cp /etc/docker/daemon.json /etc/docker/daemon.json.bak
    log "Backup created"
  fi
  
  # Generate JSON
  mirrors_json=$(printf '"%s"\n' "${selected[@]}" | paste -sd,)
  
  # Simple update (no merge, for simplicity)
  cat > /etc/docker/daemon.json <<EOF
{
  "registry-mirrors": [$mirrors_json]
}
EOF
  
  # Validate
  jq . /etc/docker/daemon.json >/dev/null || die "Invalid JSON"
  
  # Restart with retries
  log "Restarting Docker..."
  for i in $(seq 1 $DOCKER_RESTART_RETRIES); do
    systemctl restart docker && sleep 3 && break
    log "Retry $i/$DOCKER_RESTART_RETRIES..."
    sleep 5
  done
  
  systemctl is-active docker >/dev/null || die "Docker failed to start"
  
  log "Docker restarted successfully"
  
  # Test pull
  log "Testing pull..."
  docker image rm hello-world >/dev/null 2>&1 || true
  
  if docker pull hello-world >/dev/null 2>&1; then
    log "✓ Pull test passed"
  else
    log "⚠ Pull test failed (but config was updated)"
  fi
  
  # Show config
  echo
  echo "=== Configuration ==="
  cat /etc/docker/daemon.json
  echo
  
  log "Setup complete!"
  rm -f "$results"
}

main "$@"
