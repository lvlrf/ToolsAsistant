#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Iran Mirror Wizard (Ubuntu APT + pip + npm/yarn)
# Made by DrConnect
# Telegram: https://t.me/drconncet
# 
# Enhanced with English UI and progress indicators
# - Discovers known mirrors, tests latency, ranks
# - Shows numbered list and asks user to select with commas
# - Applies selected mirrors to:
#   * Ubuntu APT (deb822 .sources)
#   * pip (system-wide /etc/pip.conf)
#   * npm (global registry)
#   * yarn (global npmRegistryServer)
# ============================================================

APP_NAME="iran-mirror-wizard"
STATE_FILE="/etc/${APP_NAME}.state"
BACKUP_DIR="/etc/${APP_NAME}.backups"
DRY_RUN=0

log() { echo -e "[$(date +'%F %T')] $*"; }
warn() { echo -e "[WARN] $*" >&2; }
die() { echo -e "[ERR] $*" >&2; exit 1; }

need_root() {
  if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    die "This script must be run with sudo."
  fi
}

run_cmd() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "DRY-RUN: $*"
  else
    eval "$@"
  fi
}

have() { command -v "$1" >/dev/null 2>&1; }

detect_ubuntu() {
  [[ -r /etc/os-release ]] || die "/etc/os-release not found."
  # shellcheck disable=SC1091
  source /etc/os-release

  if [[ "${ID:-}" != "ubuntu" ]]; then
    die "This script is for Ubuntu only. (ID=${ID:-unknown})"
  fi

  UBUNTU_CODENAME="${VERSION_CODENAME:-}"
  if [[ -z "${UBUNTU_CODENAME}" ]] && have lsb_release; then
    UBUNTU_CODENAME="$(lsb_release -sc 2>/dev/null || true)"
  fi
  [[ -n "${UBUNTU_CODENAME}" ]] || die "Unable to detect Ubuntu codename."

  log "✓ Ubuntu detected: codename=${UBUNTU_CODENAME}"
}

# -----------------------------
# Known mirrors
# -----------------------------

# APT mirrors (main archive endpoints)
APT_NAMES=(
  "KubarCloud"
  "Shatel"
  "ArvanCloud"
  "IranServer"
  "IUT"
)
APT_MAIN_URLS=(
  "https://mirrors.kubarcloud.com/ubuntu/"
  "http://mirror.shatel.ir/ubuntu"
  "http://mirror.arvancloud.ir/ubuntu"
  "http://mirror.iranserver.com/ubuntu/"
  "http://repo.iut.ac.ir/repo/Ubuntu/"
)

# Security mirrors
APT_SECURITY_NAMES=(
  "Shatel (ubuntu-security)"
  "Official (security.ubuntu.com) [fallback]"
)
APT_SECURITY_URLS=(
  "http://mirror.shatel.ir/ubuntu-security"
  "http://security.ubuntu.com/ubuntu"
)

# pip mirrors
PIP_NAMES=(
  "KubarCloud (pypi.kubarcloud.com)"
  "ITO (archive.ito.gov.ir/python)"
  "Runflare (mirror-pypi.runflare.com)"
)
PIP_INDEX_URLS=(
  "https://pypi.kubarcloud.com/pypi"
  "https://archive.ito.gov.ir/python/"
  "https://mirror-pypi.runflare.com"
)

# npm registries
NPM_NAMES=(
  "KubarCloud (mirrors.kubarcloud.com/npm)"
  "ITO (archive.ito.gov.ir/npm)"
  "Runflare (mirror-npm.runflare.com)"
)
NPM_REGISTRY_URLS=(
  "https://mirrors.kubarcloud.com/npm/"
  "https://archive.ito.gov.ir/npm/"
  "https://mirror-npm.runflare.com"
)

# yarn uses npmRegistryServer
YARN_NAMES=("${NPM_NAMES[@]}")
YARN_REGISTRY_URLS=("${NPM_REGISTRY_URLS[@]}")

# -----------------------------
# Testing utilities
# -----------------------------

curl_time_ms() {
  local url="$1"
  local out
  out="$(curl -k -L -o /dev/null -sS --max-time 6 \
      -w "%{time_connect} %{time_starttransfer} %{time_total}" "$url" 2>/dev/null || true)"
  if [[ -z "$out" ]]; then
    echo ""
    return 0
  fi
  # shellcheck disable=SC2206
  local parts=($out)
  local tc="${parts[0]:-0}"
  local tt="${parts[2]:-0}"
  awk -v tc="$tc" -v tt="$tt" 'BEGIN{printf("%d %d\n", tc*1000, tt*1000)}'
}

rank_list() {
  local count="$1"
  local names_ref="$2"
  local urls_ref="$3"
  local label="$4"

  # shellcheck disable=SC1083
  local -n names="$names_ref"
  local -n urls="$urls_ref"

  # Output to stderr so it shows up but doesn't interfere with return value
  echo >&2
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
  echo "Scanning & Ranking: ${label}" >&2
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
  
  local tmp
  tmp="$(mktemp)"

  for i in $(seq 0 $((count-1))); do
    local name="${names[$i]}"
    local url="${urls[$i]}"
    local test_url="$url"
    
    if [[ "$label" == "APT(main)" ]]; then
      test_url="${url%/}/dists/${UBUNTU_CODENAME}/Release"
    elif [[ "$label" == "APT(security)" ]]; then
      test_url="${url%/}/dists/${UBUNTU_CODENAME}-security/Release"
    elif [[ "$label" == "pip" ]]; then
      test_url="${url%/}/simple/"
    elif [[ "$label" == "npm" || "$label" == "yarn" ]]; then
      test_url="${url%/}/-/ping"
    fi

    printf "  [%d/%d] Scanning: %-30s ... " "$((i+1))" "$count" "$name" >&2
    
    local times
    times="$(curl_time_ms "$test_url")"
    
    if [[ -z "$times" ]]; then
      echo "FAILED" >&2
      echo "$i|999999|DOWN|$name|$url|$test_url" >>"$tmp"
      continue
    fi

    local tc tt
    tc="$(awk '{print $1}' <<<"$times")"
    tt="$(awk '{print $2}' <<<"$times")"

    if [[ "${tt:-0}" -le 0 ]]; then
      echo "FAILED" >&2
      echo "$i|999999|DOWN|$name|$url|$test_url" >>"$tmp"
    else
      echo "OK (${tt}ms)" >&2
      echo "$i|$tt|OK|$name|$url|$test_url" >>"$tmp"
    fi
  done

  sort -t'|' -k2,2n "$tmp" > "${tmp}.sorted"

  echo >&2
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
  echo "Ranking Results: ${label}" >&2
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
  printf "%-6s | %-6s | %-10s | %-28s | %s\n" "Rank" "Status" "Time(ms)" "Name" "URL" >&2
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2

  local n=0
  while IFS='|' read -r idx t status name url test_url; do
    printf "%-6s | %-6s | %-10s | %-28s | %s\n" "$((n+1))" "$status" "$t" "$name" "$url" >&2
    echo "$((n+1))=$idx" >> "${tmp}.map"
    n=$((n+1))
  done < "${tmp}.sorted"
  
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2

  # Only return the map file path to stdout
  echo "${tmp}.map"
}

parse_selection() {
  local sel="${1:-}"
  local map_file="$2"
  local max_keep="${3:-0}"

  [[ -f "$map_file" ]] || die "map_file not found: $map_file"

  if [[ -z "${sel// /}" ]]; then
    sel="1,2"
  fi

  local chosen=()
  IFS=',' read -ra parts <<<"$sel"
  for p in "${parts[@]}"; do
    p="${p// /}"
    [[ -n "$p" ]] || continue
    [[ "$p" =~ ^[0-9]+$ ]] || die "Invalid input: $p (must be a number)"
    local line
    line="$(grep -E "^${p}=" "$map_file" || true)"
    [[ -n "$line" ]] || die "Number $p not found in list."
    local idx="${line#*=}"
    chosen+=("$idx")
  done

  local dedup=()
  local seen="|"
  for c in "${chosen[@]}"; do
    if [[ "$seen" != *"|$c|"* ]]; then
      dedup+=("$c")
      seen+=" $c|"
    fi
  done

  if [[ "$max_keep" -gt 0 ]] && [[ "${#dedup[@]}" -gt "$max_keep" ]]; then
    dedup=("${dedup[@]:0:$max_keep}")
  fi

  printf "%s\n" "${dedup[@]}"
}

# -----------------------------
# Apply configs
# -----------------------------

backup_file() {
  local f="$1"
  mkdir -p "$BACKUP_DIR"
  if [[ -f "$f" ]]; then
    local ts
    ts="$(date +%Y%m%d-%H%M%S)"
    cp -a "$f" "$BACKUP_DIR/$(basename "$f").$ts.bak"
    log "✓ Backup: $f -> $BACKUP_DIR/$(basename "$f").$ts.bak"
  fi
}

write_state() {
  mkdir -p "$(dirname "$STATE_FILE")"
  cat >"$STATE_FILE" <<EOF
# ${APP_NAME} state (generated)
UBUNTU_CODENAME=${UBUNTU_CODENAME}
APT_MAIN_SELECTED=${APT_MAIN_SELECTED:-}
APT_SECURITY_SELECTED=${APT_SECURITY_SELECTED:-}
PIP_SELECTED=${PIP_SELECTED:-}
NPM_SELECTED=${NPM_SELECTED:-}
YARN_SELECTED=${YARN_SELECTED:-}
EOF
  log "✓ State saved: $STATE_FILE"
}

apply_apt_deb822() {
  local -a main_urls=("$@")

  local -a sec_urls=()
  if [[ -n "${APT_SECURITY_SELECTED_URLS:-}" ]]; then
    # shellcheck disable=SC2206
    sec_urls=(${APT_SECURITY_SELECTED_URLS})
  fi

  if [[ " ${sec_urls[*]} " != *"http://security.ubuntu.com/ubuntu"* ]]; then
    sec_urls+=("http://security.ubuntu.com/ubuntu")
  fi

  local target="/etc/apt/sources.list.d/iran-mirrors.sources"
  mkdir -p /etc/apt/sources.list.d

  log "Applying APT configuration..."
  
  backup_file "$target"
  if [[ -f /etc/apt/sources.list ]]; then
    backup_file /etc/apt/sources.list
  fi
  if [[ -f /etc/apt/sources.list.d/ubuntu.sources ]]; then
    backup_file /etc/apt/sources.list.d/ubuntu.sources
  fi

  if [[ -f /etc/apt/sources.list.d/ubuntu.sources ]]; then
    local ts
    ts="$(date +%Y%m%d-%H%M%S)"
    run_cmd "mv /etc/apt/sources.list.d/ubuntu.sources /etc/apt/sources.list.d/ubuntu.sources.${ts}.disabled"
    log "✓ Disabled default ubuntu.sources"
  fi

  if [[ -f /etc/apt/sources.list ]]; then
    run_cmd "sed -i -E 's|^deb(\\-src)?\\s+http(s)?://(archive|security)\\.ubuntu\\.com/ubuntu|# &|g' /etc/apt/sources.list || true"
  fi

  local main_joined sec_joined
  main_joined="$(printf "%s " "${main_urls[@]}" | sed 's/[[:space:]]*$//')"
  sec_joined="$(printf "%s " "${sec_urls[@]}" | sed 's/[[:space:]]*$//')"

  cat >"$target" <<EOF
# Generated by ${APP_NAME} on $(date -u +'%F %T') UTC
# Made by DrConnect - https://t.me/drconncet
# Ubuntu codename: ${UBUNTU_CODENAME}

Types: deb deb-src
URIs: ${main_joined}
Suites: ${UBUNTU_CODENAME} ${UBUNTU_CODENAME}-updates ${UBUNTU_CODENAME}-backports
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg

Types: deb deb-src
URIs: ${sec_joined}
Suites: ${UBUNTU_CODENAME}-security
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg
EOF

  log "✓ APT sources written: $target"
  echo
  log "Updating package lists (please wait)..."
  
  if run_cmd "apt-get update -y > /tmp/apt-update.log 2>&1"; then
    log "✓ APT update completed successfully"
  else
    warn "APT update had some warnings (check /tmp/apt-update.log)"
  fi
}

apply_pip() {
  local index_url="$1"
  local pip_conf="/etc/pip.conf"
  
  log "Configuring pip..."
  backup_file "$pip_conf"

  cat >"$pip_conf" <<EOF
# Generated by iran-mirror-wizard
# Made by DrConnect - https://t.me/drconncet
[global]
index-url = ${index_url}
timeout = 30
disable-pip-version-check = true
EOF

  log "✓ pip configured: $pip_conf"
}

apply_npm() {
  local registry="$1"
  
  log "Configuring npm..."
  if ! have npm; then
    warn "npm not installed. Settings not applied. (Run later: npm config set registry \"$registry\")"
    return 0
  fi
  
  run_cmd "npm config set registry \"${registry}\" --global"
  log "✓ npm registry set: ${registry}"
}

apply_yarn() {
  local registry="$1"
  
  log "Configuring yarn..."
  if have yarn; then
    run_cmd "yarn config set npmRegistryServer \"${registry}\" --global"
    log "✓ yarn npmRegistryServer set: ${registry}"
  else
    warn "yarn not installed. Settings not applied. (Run later: yarn config set npmRegistryServer ${registry})"
  fi
}

# -----------------------------
# Main
# -----------------------------
usage() {
  cat <<EOF
Usage: sudo ./${0##*/} [--dry-run]

Iran Mirror Wizard - Configure Iranian mirrors for APT, pip, npm, and yarn
Made by DrConnect - https://t.me/drconncet

Options:
  --dry-run    Show what would be done without making changes
  --help       Show this help message
EOF
}

print_banner() {
  cat <<'EOF'
╔═══════════════════════════════════════════════════════════╗
║         Iran Mirror Wizard - Configuration Setup         ║
║                   Made by DrConnect                       ║
║              https://t.me/drconncet                       ║
╚═══════════════════════════════════════════════════════════╝
EOF
}

main() {
  if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=1
    log "DRY-RUN enabled (no changes will be applied)."
  elif [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    usage
    exit 0
  elif [[ -n "${1:-}" ]]; then
    usage
    exit 1
  fi

  need_root
  detect_ubuntu

  echo
  print_banner
  echo

  # --- Rank APT main ---
  apt_main_map="$(rank_list "${#APT_NAMES[@]}" APT_NAMES APT_MAIN_URLS "APT(main)")"
  echo
  read -r -p "APT(main): Enter mirror numbers separated by comma (default: 1,2) => " sel_apt_main
  mapfile -t apt_main_idxs < <(parse_selection "${sel_apt_main:-}" "$apt_main_map" 4)

  selected_apt_main_urls=()
  selected_apt_main_names=()
  for idx in "${apt_main_idxs[@]}"; do
    selected_apt_main_urls+=("${APT_MAIN_URLS[$idx]}")
    selected_apt_main_names+=("${APT_NAMES[$idx]}")
  done
  APT_MAIN_SELECTED="$(IFS=,; echo "${selected_apt_main_names[*]}")"

  # --- Rank APT security ---
  apt_sec_map="$(rank_list "${#APT_SECURITY_NAMES[@]}" APT_SECURITY_NAMES APT_SECURITY_URLS "APT(security)")"
  echo
  read -r -p "APT(security): Enter mirror numbers separated by comma (default: 1,2) => " sel_apt_sec
  mapfile -t apt_sec_idxs < <(parse_selection "${sel_apt_sec:-}" "$apt_sec_map" 2)

  selected_apt_sec_urls=()
  selected_apt_sec_names=()
  for idx in "${apt_sec_idxs[@]}"; do
    selected_apt_sec_urls+=("${APT_SECURITY_URLS[$idx]}")
    selected_apt_sec_names+=("${APT_SECURITY_NAMES[$idx]}")
  done
  APT_SECURITY_SELECTED="$(IFS=,; echo "${selected_apt_sec_names[*]}")"
  APT_SECURITY_SELECTED_URLS="$(printf "%s " "${selected_apt_sec_urls[@]}" | sed 's/[[:space:]]*$//')"

  # --- Rank pip mirrors ---
  pip_map="$(rank_list "${#PIP_NAMES[@]}" PIP_NAMES PIP_INDEX_URLS "pip")"
  echo
  read -r -p "pip: Enter mirror number (default: 1) => " sel_pip
  mapfile -t pip_idxs < <(parse_selection "${sel_pip:-}" "$pip_map" 1)
  pip_idx="${pip_idxs[0]}"
  PIP_SELECTED="${PIP_NAMES[$pip_idx]}"
  selected_pip_index="${PIP_INDEX_URLS[$pip_idx]}"

  # --- Rank npm registries ---
  npm_map="$(rank_list "${#NPM_NAMES[@]}" NPM_NAMES NPM_REGISTRY_URLS "npm")"
  echo
  read -r -p "npm: Enter mirror number (default: 1) => " sel_npm
  mapfile -t npm_idxs < <(parse_selection "${sel_npm:-}" "$npm_map" 1)
  npm_idx="${npm_idxs[0]}"
  NPM_SELECTED="${NPM_NAMES[$npm_idx]}"
  selected_npm_registry="${NPM_REGISTRY_URLS[$npm_idx]}"

  # --- Rank yarn registries ---
  yarn_map="$(rank_list "${#YARN_NAMES[@]}" YARN_NAMES YARN_REGISTRY_URLS "yarn")"
  echo
  read -r -p "yarn: Enter mirror number (default: 1) => " sel_yarn
  mapfile -t yarn_idxs < <(parse_selection "${sel_yarn:-}" "$yarn_map" 1)
  yarn_idx="${yarn_idxs[0]}"
  YARN_SELECTED="${YARN_NAMES[$yarn_idx]}"
  selected_yarn_registry="${YARN_REGISTRY_URLS[$yarn_idx]}"

  echo
  echo "╔═══════════════════════════════════════════════════════════╗"
  echo "║                    Selection Summary                      ║"
  echo "╚═══════════════════════════════════════════════════════════╝"
  echo
  log "APT(main):     ${APT_MAIN_SELECTED}"
  log "               => ${selected_apt_main_urls[*]}"
  echo
  log "APT(security): ${APT_SECURITY_SELECTED}"
  log "               => ${APT_SECURITY_SELECTED_URLS}"
  echo
  log "pip:           ${PIP_SELECTED}"
  log "               => ${selected_pip_index}"
  echo
  log "npm:           ${NPM_SELECTED}"
  log "               => ${selected_npm_registry}"
  echo
  log "yarn:          ${YARN_SELECTED}"
  log "               => ${selected_yarn_registry}"
  echo
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  read -r -p "Apply these settings? (y/N) => " confirm
  if [[ "${confirm,,}" != "y" ]]; then
    warn "Cancelled by user."
    exit 0
  fi

  echo
  echo "╔═══════════════════════════════════════════════════════════╗"
  echo "║              Applying Configuration Changes               ║"
  echo "╚═══════════════════════════════════════════════════════════╝"
  echo

  mkdir -p "$BACKUP_DIR"

  apply_apt_deb822 "${selected_apt_main_urls[@]}"
  echo
  apply_pip "$selected_pip_index"
  echo
  apply_npm "$selected_npm_registry"
  echo
  apply_yarn "$selected_yarn_registry"
  echo

  write_state

  echo
  echo "╔═══════════════════════════════════════════════════════════╗"
  echo "║                  ✓ Configuration Complete                 ║"
  echo "║                   Made by DrConnect                       ║"
  echo "║              https://t.me/drconncet                       ║"
  echo "╚═══════════════════════════════════════════════════════════╝"
  echo
  log "All Iranian mirrors have been configured successfully!"
  log "Backups saved to: $BACKUP_DIR"
  echo
}

main "$@"