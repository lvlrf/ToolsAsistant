#!/usr/bin/env bash
set -euo pipefail

# ================================================================
# DNS Anti-403 Manager - Professional Edition
# Developed by: DrConnect
# Telegram: @lvlrf (t.me/lvlrf)
# Mobile: +98 912 741 9412
# For professional services, contact us!
# ================================================================

VERSION="4.0-pro"
BACKUP_DIR="/root/dns-backups"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# Test targets
TARGETS=(
  "Google|https://google.com"
  "GitHub|https://github.com"
  "DockerHub|https://registry-1.docker.io/v2/"
)

# Iranian DNS servers
IRANIAN_DNS=(
  "Shecan1|178.22.122.100"
  "Shecan2|185.51.200.2"
  "Beshkan1|181.41.194.177"
  "Beshkan2|181.41.194.186"
  "Begzar1|185.55.226.26"
  "Begzar2|185.55.225.25"
  "Begzar3|185.55.224.24"
  "Electro1|78.157.42.100"
  "Electro2|78.157.42.101"
  "Radar1|10.202.10.10"
  "Radar2|10.202.10.11"
  "403online-1|10.202.10.202"
  "403online-2|10.202.10.102"
  "DynX-AntiSan1|10.139.177.18"
  "DynX-AntiSan2|10.139.177.16"
  "DynX-Vanilla1|10.139.177.21"
  "DynX-Vanilla2|10.139.177.22"
  "DynX-Adblock1|109.70.74.38"
  "DynX-Adblock2|109.70.74.68"
  "HostIran1|172.29.0.100"
  "HostIran2|172.29.2.100"
  "Moomni1|37.32.5.60"
  "Moomni2|37.32.5.61"
)

# All DNS servers (Iranian + International)
ALL_DNS=(
  # Iranian DNS
  "Shecan1|178.22.122.100"
  "Shecan2|185.51.200.2"
  "Beshkan1|181.41.194.177"
  "Beshkan2|181.41.194.186"
  "Begzar1|185.55.226.26"
  "Begzar2|185.55.225.25"
  "Begzar3|185.55.224.24"
  "Electro1|78.157.42.100"
  "Electro2|78.157.42.101"
  "Radar1|10.202.10.10"
  "Radar2|10.202.10.11"
  "403online-1|10.202.10.202"
  "403online-2|10.202.10.102"
  "DynX-AntiSan1|10.139.177.18"
  "DynX-AntiSan2|10.139.177.16"
  "DynX-Vanilla1|10.139.177.21"
  "DynX-Vanilla2|10.139.177.22"
  "DynX-Adblock1|109.70.74.38"
  "DynX-Adblock2|109.70.74.68"
  "HostIran1|172.29.0.100"
  "HostIran2|172.29.2.100"
  "Moomni1|37.32.5.60"
  "Moomni2|37.32.5.61"
  
  # AdGuard DNS (Russia)
  "AdGuard-Default1|94.140.14.14"
  "AdGuard-Default2|94.140.14.15"
  "AdGuard-New1|94.140.14.49"
  "AdGuard-New2|94.140.14.59"
  "AdGuard-NonFilter1|94.140.14.140"
  "AdGuard-NonFilter2|94.140.14.141"
  
  # Quad9 (Switzerland)
  "Quad9-Primary|9.9.9.9"
  "Quad9-Secondary|149.112.112.112"
  "Quad9-Unsecured|9.9.9.10"
  "Quad9-ECS|9.9.9.11"
  
  # Cloudflare
  "Cloudflare-Primary|1.1.1.1"
  "Cloudflare-Secondary|1.0.0.1"
  "Cloudflare-Family1|1.1.1.3"
  "Cloudflare-Family2|1.0.0.3"
  "Cloudflare-NoMalware|1.1.1.2"
  
  # NextDNS
  "NextDNS-Primary|45.90.28.0"
  "NextDNS-Secondary|45.90.30.0"
  "NextDNS-Anycast1|45.90.28.167"
  "NextDNS-Anycast2|45.90.30.167"
  
  # Control D (Canada)
  "ControlD-Unfiltered1|76.76.2.0"
  "ControlD-Unfiltered2|76.76.10.0"
  "ControlD-BlockMalware1|76.76.2.1"
  "ControlD-BlockMalware2|76.76.10.1"
  
  # CleanBrowsing
  "CleanBrowsing-Security|185.228.168.9"
  "CleanBrowsing-Adult|185.228.168.10"
  "CleanBrowsing-Family|185.228.168.168"
  
  # OpenDNS
  "OpenDNS-Home1|208.67.222.222"
  "OpenDNS-Home2|208.67.220.220"
  "OpenDNS-Family1|208.67.222.123"
  "OpenDNS-Family2|208.67.220.123"
  
  # DNS.SB
  "DNS.SB-Primary|185.222.222.222"
  "DNS.SB-Secondary|45.11.45.11"
  
  # Alternate DNS
  "AlternateDNS1|76.76.19.19"
  "AlternateDNS2|76.223.122.150"
  
  # Comodo
  "Comodo-Primary|8.26.56.26"
  "Comodo-Secondary|8.20.247.20"
  
  # Verisign
  "Verisign-Primary|64.6.64.6"
  "Verisign-Secondary|64.6.65.6"
  
  # BlahDNS
  "BlahDNS-Switzerland|45.91.92.121"
  "BlahDNS-Finland|95.216.212.177"
  "BlahDNS-Germany|78.46.244.143"
  "BlahDNS-Singapore|139.162.112.47"
  
  # Canadian Shield
  "CanadianShield-Private|149.112.121.10"
  "CanadianShield-Protected|149.112.121.20"
  "CanadianShield-Family|149.112.121.30"
  
  # Applied Privacy (Austria)
  "Applied-Privacy|37.252.185.232"
  
  # CZ.NIC (Czech)
  "CZ.NIC-Primary|193.17.47.1"
  "CZ.NIC-Secondary|185.43.135.1"
  
  # Others
  "HurricaneElectric|74.82.42.42"
  "puntCAT|109.69.8.51"
  "Digitale-Gesellschaft|185.95.218.42"
  "DNS-Privacy-DE|46.182.19.48"
  "UncensoredDNS1|91.239.100.100"
  "UncensoredDNS2|89.233.43.71"
  
  # Google
  "Google-Primary|8.8.8.8"
  "Google-Secondary|8.8.4.4"
)

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_ok() { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Utility functions
need_cmd() { command -v "$1" >/dev/null 2>&1; }

ensure_deps() {
  local pkgs=()
  need_cmd curl || pkgs+=("curl")
  need_cmd dig || pkgs+=("dnsutils")
  need_cmd resolvectl || pkgs+=("systemd")

  if [[ "${#pkgs[@]}" -gt 0 ]]; then
    log_info "Installing dependencies: ${pkgs[*]}"
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y >/dev/null 2>&1 || true
    apt-get install -y "${pkgs[@]}" >/dev/null 2>&1 || true
  fi
}

get_interface() {
  local iface=""
  iface="$(ip route show default 2>/dev/null | awk '{print $5}' | head -n1 || true)"
  if [[ -n "$iface" ]]; then
    echo "$iface"
    return 0
  fi
  return 1
}

check_dns_alive() {
  local dns_ip="$1"
  timeout 3 dig +time=2 +tries=1 @"$dns_ip" google.com >/dev/null 2>&1
}

verdict() {
  case "$1" in
    200|204|301|302|307|308|401) echo "OK" ;;
    403) echo "BLOCK" ;;
    000) echo "FAIL" ;;
    *) echo "WARN" ;;
  esac
}

test_dns_proper() {
  local name="$1" dnsip="$2" iface="$3"
  local pass=0 block=0 fail=0

  resolvectl dns "$iface" "$dnsip" >/dev/null 2>&1
  resolvectl domain "$iface" "~." >/dev/null 2>&1
  sleep 2

  for t in "${TARGETS[@]}"; do
    label="${t%%|*}"
    url="${t#*|}"
    
    code=$(timeout 15 curl -sS -L --max-time 15 -o /dev/null \
      -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    v=$(verdict "$code")
    case "$v" in
      OK) pass=$((pass+1)) ;;
      BLOCK) block=$((block+1)) ;;
      *) fail=$((fail+1)) ;;
    esac
  done

  local status="WEAK"
  if [[ $block -gt 0 ]]; then
    status="BLOCKED(403)"
  elif [[ $pass -eq ${#TARGETS[@]} ]]; then
    status="PERFECT"
  elif [[ $pass -ge $((${#TARGETS[@]}-1)) ]]; then
    status="GOOD"
  fi

  local score=$((block*10000 + fail*2000 + (${#TARGETS[@]}-pass)*500))
  echo "$score|$status|$name|$dnsip|$pass|$block|$fail"
}

# Banner
show_banner() {
  clear
  echo -e "${CYAN}"
  cat << "EOF"
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║         ██████╗ ███╗   ██╗███████╗    ██╗  ██╗ ██████╗ ██████╗  ║
║         ██╔══██╗████╗  ██║██╔════╝    ██║  ██║██╔═████╗╚════██╗ ║
║         ██║  ██║██╔██╗ ██║███████╗    ███████║██║██╔██║ █████╔╝ ║
║         ██║  ██║██║╚██╗██║╚════██║    ╚════██║████╔╝██║ ╚═══██╗ ║
║         ██████╔╝██║ ╚████║███████║         ██║╚██████╔╝██████╔╝ ║
║         ╚═════╝ ╚═╝  ╚═══╝╚══════╝         ╚═╝ ╚═════╝ ╚═════╝  ║
║                                                                  ║
║              Anti-403 DNS Manager - Professional Edition         ║
║                         Version 4.0                              ║
╚══════════════════════════════════════════════════════════════════╝
EOF
  echo -e "${NC}"
  echo -e "${MAGENTA}╔══════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${MAGENTA}║${NC}  ${BOLD}Developed by: DrConnect${NC}                                       ${MAGENTA}║${NC}"
  echo -e "${MAGENTA}║${NC}  ${GREEN}Telegram:${NC} @lvlrf (t.me/lvlrf)                                 ${MAGENTA}║${NC}"
  echo -e "${MAGENTA}║${NC}  ${GREEN}Mobile:${NC} +98 912 741 9412                                      ${MAGENTA}║${NC}"
  echo -e "${MAGENTA}║${NC}                                                                  ${MAGENTA}║${NC}"
  echo -e "${MAGENTA}║${NC}  ${YELLOW}For professional network services, contact us!${NC}               ${MAGENTA}║${NC}"
  echo -e "${MAGENTA}╚══════════════════════════════════════════════════════════════════╝${NC}"
  echo
}

# Show current DNS
show_current_dns() {
  local iface=""
  if ! iface=$(get_interface); then
    log_error "Cannot detect network interface!"
    return 1
  fi
  
  echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║${NC}                    ${BOLD}Current DNS Configuration${NC}                    ${CYAN}║${NC}"
  echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════╝${NC}"
  echo
  echo -e "${BLUE}Interface:${NC} $iface"
  echo
  
  local dns_servers=""
  dns_servers=$(resolvectl status "$iface" 2>/dev/null | grep "DNS Servers" | head -1 | awk '{$1=$2=""; print $0}' | sed 's/^[ \t]*//' || echo "None")
  
  if [[ -n "$dns_servers" && "$dns_servers" != "None" ]]; then
    echo -e "${GREEN}DNS Servers:${NC}"
    for dns in $dns_servers; do
      echo -e "  ${YELLOW}•${NC} $dns"
    done
  else
    echo -e "${YELLOW}No DNS servers configured${NC}"
  fi
  
  echo
  resolvectl status "$iface" 2>/dev/null | grep -A 10 "DNS Servers" || true
  echo
}

# Test DNS function
run_dns_test() {
  local dns_list=("$@")
  local list_name="$1"
  shift
  dns_list=("$@")
  
  local iface=""
  if ! iface=$(get_interface); then
    log_error "Cannot detect network interface!"
    return 1
  fi
  
  local current_dns=""
  current_dns=$(resolvectl status "$iface" 2>/dev/null | grep "DNS Servers" | head -1 | awk '{print $3, $4, $5, $6}' || echo "")
  
  mkdir -p "$BACKUP_DIR"
  local backup_file="$BACKUP_DIR/dns-state-$(date +%s).txt"
  resolvectl status > "$backup_file" 2>/dev/null || true
  
  echo
  echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║${NC}                    ${BOLD}Testing $list_name DNS Servers${NC}                ${CYAN}║${NC}"
  echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════╝${NC}"
  echo
  log_info "Interface: $iface"
  log_info "Testing ${#dns_list[@]} DNS servers"
  log_info "This may take a few minutes..."
  echo
  
  local tmp=$(mktemp)
  local tested=0
  local skipped=0
  local total="${#dns_list[@]}"
  
  for item in "${dns_list[@]}"; do
    name="${item%%|*}"
    dnsip="${item#*|}"
    
    echo -ne "\r${BLUE}[CHECK]${NC} $name ($dnsip)...                    "
    
    if ! check_dns_alive "$dnsip"; then
      echo -e "\r${CYAN}[SKIP]${NC} $name ($dnsip) - Not reachable          "
      skipped=$((skipped+1))
      continue
    fi
    
    tested=$((tested+1))
    echo -ne "\r${BLUE}[$tested/$total]${NC} Testing $name ($dnsip)...        "
    
    result=$(test_dns_proper "$name" "$dnsip" "$iface")
    echo "$result" >> "$tmp"
    
    echo -e "\r${GREEN}[$tested/$total]${NC} Tested $name ($dnsip)           "
  done
  
  # Restore DNS
  resolvectl dns "$iface" $current_dns 2>/dev/null || true
  resolvectl domain "$iface" "~." 2>/dev/null || true
  
  echo
  log_ok "Testing complete! Tested: $tested | Skipped: $skipped"
  echo
  
  if [[ ! -s "$tmp" ]]; then
    log_warn "No DNS servers were reachable!"
    rm -f "$tmp"
    return 0
  fi
  
  # Sort results
  local tmp_sorted=$(mktemp)
  sort -t'|' -k1,1n "$tmp" > "$tmp_sorted"
  
  # Display results
  local ts=$(date +%F_%H%M%S)
  local report="/root/dns-test-${ts}.txt"
  
  {
    echo "════════════════════════════════════════════════════════════════════"
    echo "                    DNS Test Results - $list_name"
    echo "════════════════════════════════════════════════════════════════════"
    echo "Time: $(date)"
    echo "Tested: $tested DNS | Skipped: $skipped"
    echo
    printf "%-4s %-16s %-24s %-18s %-3s %-3s %-3s\n" \
      "No" "STATUS" "DNS" "IP" "OK" "403" "FAIL"
    echo "────────────────────────────────────────────────────────────────────"
    
    i=0
    while IFS='|' read -r score status name ip ok b403 fail; do
      i=$((i+1))
      printf "%-4s %-16s %-24s %-18s %-3s %-3s %-3s\n" \
        "$i)" "$status" "$name" "$ip" "$ok" "$b403" "$fail"
    done < "$tmp_sorted"
    
    echo
    echo "Legend:"
    echo "  ✓ PERFECT: All tests passed - Bypasses 403!"
    echo "  ✓ GOOD: Minor issues, no 403 blocking"
    echo "  ✗ BLOCKED: Has 403 errors - Cannot bypass"
    echo "  ! WEAK: Multiple failures"
    echo
  } | tee "$report"
  
  log_ok "Report saved: $report"
  echo
  
  # Interactive selection
  local total_tested=$(wc -l < "$tmp_sorted")
  
  while true; do
    echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║${NC}                   ${BOLD}Apply DNS Configuration${NC}                      ${YELLOW}║${NC}"
    echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo "Select DNS to apply:"
    echo "  • Single DNS: 1"
    echo "  • Primary + Secondary: 1,2"
    echo "  • Skip: 0"
    echo
    read -r -p "Your choice: " choice
    
    choice="$(echo "${choice:-}" | tr -d '[:space:]')"
    
    if [[ "$choice" == "0" ]]; then
      log_info "No changes made"
      rm -f "$tmp" "$tmp_sorted"
      return 0
    fi
    
    IFS=',' read -r idx1 idx2 <<<"$choice"
    
    if ! [[ "$idx1" =~ ^[0-9]+$ ]] || [[ "$idx1" -lt 1 ]] || [[ "$idx1" -gt "$total_tested" ]]; then
      log_error "Invalid selection! Please enter a number between 1 and $total_tested"
      echo
      continue
    fi
    
    dns1_line="$(sed -n "${idx1}p" "$tmp_sorted")"
    dns1_ip="$(echo "$dns1_line" | cut -d'|' -f4)"
    dns1_name="$(echo "$dns1_line" | cut -d'|' -f3)"
    dns1_status="$(echo "$dns1_line" | cut -d'|' -f2)"
    
    dns2_ip=""
    dns2_name=""
    dns2_status=""
    
    if [[ -n "${idx2:-}" ]]; then
      if ! [[ "$idx2" =~ ^[0-9]+$ ]] || [[ "$idx2" -lt 1 ]] || [[ "$idx2" -gt "$total_tested" ]]; then
        log_error "Invalid secondary DNS! Please try again"
        echo
        continue
      fi
      
      dns2_line="$(sed -n "${idx2}p" "$tmp_sorted")"
      dns2_ip="$(echo "$dns2_line" | cut -d'|' -f4)"
      dns2_name="$(echo "$dns2_line" | cut -d'|' -f3)"
      dns2_status="$(echo "$dns2_line" | cut -d'|' -f2)"
    fi
    
    echo
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}                      ${BOLD}Your Selection${NC}                             ${GREEN}║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "  ${BOLD}Primary DNS:${NC}"
    echo -e "    $idx1) $dns1_name ($dns1_ip) - $dns1_status"
    if [[ -n "$dns2_ip" ]]; then
      echo -e "  ${BOLD}Secondary DNS:${NC}"
      echo -e "    $idx2) $dns2_name ($dns2_ip) - $dns2_status"
    fi
    echo
    
    if [[ "$dns1_status" == "BLOCKED(403)" ]] || [[ "$dns2_status" == "BLOCKED(403)" ]]; then
      log_warn "Warning: Selected DNS has 403 errors!"
      echo
    fi
    
    while true; do
      read -r -p "Apply these DNS settings? (y/n): " confirm
      confirm="${confirm,,}"
      
      if [[ "$confirm" == "y" ]]; then
        break 2
      elif [[ "$confirm" == "n" ]]; then
        echo
        break
      else
        log_error "Please enter 'y' or 'n'"
      fi
    done
  done
  
  # Apply DNS
  echo
  log_info "Applying DNS settings..."
  
  if [[ -n "$dns2_ip" ]]; then
    resolvectl dns "$iface" "$dns1_ip" "$dns2_ip"
    log_ok "DNS set: $dns1_ip (primary), $dns2_ip (secondary)"
  else
    resolvectl dns "$iface" "$dns1_ip"
    log_ok "DNS set: $dns1_ip"
  fi
  
  resolvectl domain "$iface" "~."
  
  echo
  log_ok "DNS applied successfully!"
  echo
  
  # Test
  log_info "Testing new DNS configuration..."
  echo -n "  • Google: "
  if curl -sS --max-time 5 -o /dev/null https://google.com 2>/dev/null; then
    echo -e "${GREEN}✓ OK${NC}"
  else
    echo -e "${RED}✗ FAIL${NC}"
  fi
  
  echo -n "  • GitHub: "
  code=$(curl -sS --max-time 10 -o /dev/null -w "%{http_code}" https://github.com 2>/dev/null || echo "000")
  if [[ "$code" == "200" ]]; then
    echo -e "${GREEN}✓ OK${NC}"
  elif [[ "$code" == "403" ]]; then
    echo -e "${RED}✗ BLOCKED (403)${NC}"
  else
    echo -e "${YELLOW}! HTTP $code${NC}"
  fi
  
  echo -n "  • Docker: "
  code=$(curl -sS --max-time 10 -o /dev/null -w "%{http_code}" https://registry-1.docker.io/v2/ 2>/dev/null || echo "000")
  if [[ "$code" == "401" ]]; then
    echo -e "${GREEN}✓ OK (401 - Normal)${NC}"
  elif [[ "$code" == "403" ]]; then
    echo -e "${RED}✗ BLOCKED (403)${NC}"
  else
    echo -e "${YELLOW}! HTTP $code${NC}"
  fi
  
  echo
  
  # Permanent option
  while true; do
    read -r -p "Make DNS permanent? (y/n): " make_permanent
    make_permanent="${make_permanent,,}"
    
    if [[ "$make_permanent" == "y" ]]; then
      echo
      log_info "Making DNS permanent..."
      
      if [[ -f /etc/systemd/resolved.conf ]]; then
        cp /etc/systemd/resolved.conf "/etc/systemd/resolved.conf.backup.$(date +%s)"
        log_ok "Backed up config"
      fi
      
      if grep -q "^\[Resolve\]" /etc/systemd/resolved.conf 2>/dev/null; then
        sed -i '/^DNS=/d' /etc/systemd/resolved.conf
        sed -i '/^Domains=/d' /etc/systemd/resolved.conf
        
        if [[ -n "$dns2_ip" ]]; then
          sed -i "/^\[Resolve\]/a DNS=$dns1_ip $dns2_ip" /etc/systemd/resolved.conf
        else
          sed -i "/^\[Resolve\]/a DNS=$dns1_ip" /etc/systemd/resolved.conf
        fi
        sed -i "/^\[Resolve\]/a Domains=~." /etc/systemd/resolved.conf
      else
        {
          echo ""
          echo "[Resolve]"
          if [[ -n "$dns2_ip" ]]; then
            echo "DNS=$dns1_ip $dns2_ip"
          else
            echo "DNS=$dns1_ip"
          fi
          echo "Domains=~."
        } >> /etc/systemd/resolved.conf
      fi
      
      systemctl restart systemd-resolved
      sleep 2
      
      log_ok "DNS is now permanent!"
      break
      
    elif [[ "$make_permanent" == "n" ]]; then
      echo
      log_info "DNS is temporary (will reset after reboot)"
      break
    else
      log_error "Please enter 'y' or 'n'"
    fi
  done
  
  rm -f "$tmp" "$tmp_sorted"
}

# Manual DNS setup
manual_dns_setup() {
  local iface=""
  if ! iface=$(get_interface); then
    log_error "Cannot detect network interface!"
    return 1
  fi
  
  echo
  echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║${NC}                    ${BOLD}Manual DNS Configuration${NC}                     ${CYAN}║${NC}"
  echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════╝${NC}"
  echo
  
  # Show all DNS list
  echo -e "${YELLOW}Available DNS Servers:${NC}"
  echo
  
  i=0
  for item in "${ALL_DNS[@]}"; do
    i=$((i+1))
    name="${item%%|*}"
    ip="${item#*|}"
    printf "  ${CYAN}%3d)${NC} %-28s ${GREEN}%s${NC}\n" "$i" "$name" "$ip"
    
    if (( i % 20 == 0 )); then
      echo
      read -r -p "Press Enter to see more..." dummy
      echo
    fi
  done
  
  echo
  total=${#ALL_DNS[@]}
  
  while true; do
    echo -e "${YELLOW}Select DNS (or 0 to cancel):${NC}"
    echo "  • Single DNS: 1"
    echo "  • Primary + Secondary: 1,2"
    echo "  • Cancel: 0"
    echo
    read -r -p "Your choice: " choice
    
    choice="$(echo "${choice:-}" | tr -d '[:space:]')"
    
    if [[ "$choice" == "0" ]]; then
      log_info "Cancelled"
      return 0
    fi
    
    IFS=',' read -r idx1 idx2 <<<"$choice"
    
    if ! [[ "$idx1" =~ ^[0-9]+$ ]] || [[ "$idx1" -lt 1 ]] || [[ "$idx1" -gt "$total" ]]; then
      log_error "Invalid selection! Please enter a number between 1 and $total"
      echo
      continue
    fi
    
    dns1_item="${ALL_DNS[$((idx1-1))]}"
    dns1_name="${dns1_item%%|*}"
    dns1_ip="${dns1_item#*|}"
    
    dns2_ip=""
    dns2_name=""
    
    if [[ -n "${idx2:-}" ]]; then
      if ! [[ "$idx2" =~ ^[0-9]+$ ]] || [[ "$idx2" -lt 1 ]] || [[ "$idx2" -gt "$total" ]]; then
        log_error "Invalid secondary DNS! Please try again"
        echo
        continue
      fi
      
      dns2_item="${ALL_DNS[$((idx2-1))]}"
      dns2_name="${dns2_item%%|*}"
      dns2_ip="${dns2_item#*|}"
    fi
    
    echo
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}                      ${BOLD}Your Selection${NC}                             ${GREEN}║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "  ${BOLD}Primary DNS:${NC}"
    echo -e "    $idx1) $dns1_name ($dns1_ip)"
    if [[ -n "$dns2_ip" ]]; then
      echo -e "  ${BOLD}Secondary DNS:${NC}"
      echo -e "    $idx2) $dns2_name ($dns2_ip)"
    fi
    echo
    
    while true; do
      read -r -p "Apply these DNS settings? (y/n): " confirm
      confirm="${confirm,,}"
      
      if [[ "$confirm" == "y" ]]; then
        break 2
      elif [[ "$confirm" == "n" ]]; then
        echo
        break
      else
        log_error "Please enter 'y' or 'n'"
      fi
    done
  done
  
  # Apply
  echo
  log_info "Applying DNS settings..."
  
  if [[ -n "$dns2_ip" ]]; then
    resolvectl dns "$iface" "$dns1_ip" "$dns2_ip"
    log_ok "DNS set: $dns1_ip (primary), $dns2_ip (secondary)"
  else
    resolvectl dns "$iface" "$dns1_ip"
    log_ok "DNS set: $dns1_ip"
  fi
  
  resolvectl domain "$iface" "~."
  
  echo
  log_ok "DNS applied successfully!"
  echo
  
  # Test
  log_info "Testing new DNS configuration..."
  echo -n "  • Google: "
  if curl -sS --max-time 5 -o /dev/null https://google.com 2>/dev/null; then
    echo -e "${GREEN}✓ OK${NC}"
  else
    echo -e "${RED}✗ FAIL${NC}"
  fi
  
  echo -n "  • GitHub: "
  code=$(curl -sS --max-time 10 -o /dev/null -w "%{http_code}" https://github.com 2>/dev/null || echo "000")
  if [[ "$code" == "200" ]]; then
    echo -e "${GREEN}✓ OK${NC}"
  elif [[ "$code" == "403" ]]; then
    echo -e "${RED}✗ BLOCKED (403)${NC}"
  else
    echo -e "${YELLOW}! HTTP $code${NC}"
  fi
  
  echo -n "  • Docker: "
  code=$(curl -sS --max-time 10 -o /dev/null -w "%{http_code}" https://registry-1.docker.io/v2/ 2>/dev/null || echo "000")
  if [[ "$code" == "401" ]]; then
    echo -e "${GREEN}✓ OK (401 - Normal)${NC}"
  elif [[ "$code" == "403" ]]; then
    echo -e "${RED}✗ BLOCKED (403)${NC}"
  else
    echo -e "${YELLOW}! HTTP $code${NC}"
  fi
  
  echo
  
  # Permanent option
  while true; do
    read -r -p "Make DNS permanent? (y/n): " make_permanent
    make_permanent="${make_permanent,,}"
    
    if [[ "$make_permanent" == "y" ]]; then
      echo
      log_info "Making DNS permanent..."
      
      if [[ -f /etc/systemd/resolved.conf ]]; then
        cp /etc/systemd/resolved.conf "/etc/systemd/resolved.conf.backup.$(date +%s)"
        log_ok "Backed up config"
      fi
      
      if grep -q "^\[Resolve\]" /etc/systemd/resolved.conf 2>/dev/null; then
        sed -i '/^DNS=/d' /etc/systemd/resolved.conf
        sed -i '/^Domains=/d' /etc/systemd/resolved.conf
        
        if [[ -n "$dns2_ip" ]]; then
          sed -i "/^\[Resolve\]/a DNS=$dns1_ip $dns2_ip" /etc/systemd/resolved.conf
        else
          sed -i "/^\[Resolve\]/a DNS=$dns1_ip" /etc/systemd/resolved.conf
        fi
        sed -i "/^\[Resolve\]/a Domains=~." /etc/systemd/resolved.conf
      else
        {
          echo ""
          echo "[Resolve]"
          if [[ -n "$dns2_ip" ]]; then
            echo "DNS=$dns1_ip $dns2_ip"
          else
            echo "DNS=$dns1_ip"
          fi
          echo "Domains=~."
        } >> /etc/systemd/resolved.conf
      fi
      
      systemctl restart systemd-resolved
      sleep 2
      
      log_ok "DNS is now permanent!"
      break
      
    elif [[ "$make_permanent" == "n" ]]; then
      echo
      log_info "DNS is temporary (will reset after reboot)"
      break
    else
      log_error "Please enter 'y' or 'n'"
    fi
  done
}

# Main menu
main_menu() {
  while true; do
    show_banner
    
    echo -e "${BOLD}Main Menu:${NC}"
    echo
    echo -e "  ${CYAN}1)${NC} Show Current DNS Configuration"
    echo -e "  ${CYAN}2)${NC} Test Iranian DNS Servers"
    echo -e "  ${CYAN}3)${NC} Test All DNS Servers (Iranian + International)"
    echo -e "  ${CYAN}4)${NC} Manual DNS Setup (No Testing)"
    echo -e "  ${CYAN}5)${NC} Exit"
    echo
    
    while true; do
      read -r -p "Select an option [1-5]: " choice
      
      case "$choice" in
        1)
          show_current_dns
          ;;
        2)
          run_dns_test "Iranian" "${IRANIAN_DNS[@]}"
          ;;
        3)
          run_dns_test "All" "${ALL_DNS[@]}"
          ;;
        4)
          manual_dns_setup
          ;;
        5)
          echo
          echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
          echo -e "${GREEN}║${NC}              ${BOLD}Thank you for using DNS Anti-403 Manager!${NC}         ${GREEN}║${NC}"
          echo -e "${GREEN}║${NC}                                                                  ${GREEN}║${NC}"
          echo -e "${GREEN}║${NC}  ${CYAN}For professional services, contact DrConnect:${NC}              ${GREEN}║${NC}"
          echo -e "${GREEN}║${NC}  ${YELLOW}Telegram:${NC} @lvlrf (t.me/lvlrf)                                 ${GREEN}║${NC}"
          echo -e "${GREEN}║${NC}  ${YELLOW}Mobile:${NC} +98 912 741 9412                                      ${GREEN}║${NC}"
          echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
          echo
          exit 0
          ;;
        *)
          log_error "Invalid option! Please select 1-5"
          echo
          continue
          ;;
      esac
      
      echo
      read -r -p "Press Enter to continue..." dummy
      break
    done
  done
}

# Entry point
if [[ $EUID -ne 0 ]]; then
  echo -e "${RED}[ERROR]${NC} This script must be run with sudo/root privileges"
  exit 1
fi

if ! systemctl is-active --quiet systemd-resolved; then
  echo -e "${RED}[ERROR]${NC} systemd-resolved is not active!"
  echo "Please ensure systemd-resolved is running"
  exit 1
fi

ensure_deps
main_menu
