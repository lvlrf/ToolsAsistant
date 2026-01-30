#!/usr/bin/env python3
"""
داشبورد مانیتورینگ Sub-Relay
نمایش وضعیت سرویس‌ها، اتصالات، و امکان تغییر مدل
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# مسیر کانفیگ
CONFIG_PATH = Path("/opt/sub-relay/config.env")
if not CONFIG_PATH.exists():
    CONFIG_PATH = Path(__file__).parent.parent / "config.env"

load_dotenv(CONFIG_PATH)

app = FastAPI(title="Sub-Relay Dashboard", docs_url=None, redoc_url=None)
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# --- بارگذاری تنظیمات از config.env ---
ACTIVE_MODE = os.getenv("ACTIVE_MODE", "unknown")
PANEL_URL = os.getenv("PANEL_URL", "")
SUB_DOMAIN = os.getenv("SUB_DOMAIN", "")
SUB_PATH = os.getenv("SUB_PATH", "/sub/")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", 8080))
WG_SERVER_IP = os.getenv("WG_SERVER_IP", "10.66.66.1")
XRAY_SOCKS_PORT = int(os.getenv("XRAY_SOCKS_PORT", 1080))


async def check_connectivity(url: str, timeout: float = 5.0, proxy: str = None) -> dict:
    """
    چک کردن اتصال به یک URL
    
    Args:
        url: آدرس برای چک کردن
        timeout: زمان timeout
        proxy: آدرس پروکسی (اختیاری)
    
    Returns:
        دیکشنری شامل وضعیت و اطلاعات اتصال
    """
    try:
        async with httpx.AsyncClient(proxy=proxy, timeout=timeout, verify=False) as client:
            start = datetime.now()
            resp = await client.get(url)
            latency = (datetime.now() - start).total_seconds() * 1000
            return {
                "status": "ok",
                "code": resp.status_code,
                "latency_ms": round(latency, 2)
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)[:100]  # محدود کردن طول خطا
        }


def check_service_status(service_name: str) -> dict:
    """
    چک کردن وضعیت یک سرویس systemd
    
    Args:
        service_name: نام سرویس
    
    Returns:
        دیکشنری شامل نام سرویس و وضعیت فعال/غیرفعال
    """
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        is_active = result.stdout.strip() == "active"
        return {"service": service_name, "active": is_active}
    except Exception as e:
        return {"service": service_name, "active": False, "error": str(e)}


def check_wireguard_status() -> dict:
    """
    چک کردن وضعیت WireGuard و اتصال peer
    
    Returns:
        دیکشنری شامل وضعیت و جزئیات اتصال
    """
    try:
        result = subprocess.run(
            ["wg", "show", "wg0"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            output = result.stdout
            # بررسی وجود handshake (نشانه اتصال موفق)
            has_handshake = "latest handshake" in output
            return {
                "status": "up",
                "connected": has_handshake,
                "details": output[:500]  # محدود کردن خروجی
            }
        return {"status": "down", "connected": False}
    except Exception as e:
        return {"status": "error", "error": str(e), "connected": False}


def check_xray_socks() -> dict:
    """
    چک کردن اینکه پورت SOCKS5 در حال گوش دادن است
    
    Returns:
        دیکشنری شامل وضعیت پورت
    """
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', XRAY_SOCKS_PORT))
        sock.close()
        return {"port": XRAY_SOCKS_PORT, "listening": result == 0}
    except Exception as e:
        return {"port": XRAY_SOCKS_PORT, "listening": False, "error": str(e)}


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """صفحه اصلی داشبورد"""
    
    # بارگذاری مجدد تنظیمات (برای گرفتن آخرین تغییرات)
    load_dotenv(CONFIG_PATH, override=True)
    mode = os.getenv("ACTIVE_MODE", "unknown")
    
    # جمع‌آوری وضعیت سرویس‌ها
    services = {
        "haproxy": check_service_status("haproxy"),
    }
    
    # سرویس‌های وابسته به مدل
    if mode == "wireguard":
        services["wireguard"] = check_service_status("wg-quick@wg0")
    elif mode == "xray":
        services["xray"] = check_service_status("xray-client")
        services["nginx"] = check_service_status("nginx")
    
    # جمع‌آوری وضعیت اتصالات
    connectivity = {}
    
    # چک گوگل (مستقیم)
    connectivity["google_direct"] = await check_connectivity("https://www.google.com", timeout=3)
    
    # چک بسته به مدل
    if mode == "wireguard":
        wg_status = check_wireguard_status()
        connectivity["tunnel"] = wg_status
        
        # چک پنل از طریق IP وایرگارد
        if wg_status.get("connected"):
            connectivity["panel"] = await check_connectivity(
                f"https://{WG_SERVER_IP}",
                timeout=5
            )
        else:
            connectivity["panel"] = {
                "status": "error",
                "error": "WireGuard tunnel not connected"
            }
            
    elif mode == "xray":
        xray_status = check_xray_socks()
        connectivity["tunnel"] = xray_status
        
        # چک پنل از طریق SOCKS5
        if xray_status.get("listening"):
            connectivity["panel"] = await check_connectivity(
                PANEL_URL,
                proxy=f"socks5://127.0.0.1:{XRAY_SOCKS_PORT}",
                timeout=5
            )
        else:
            connectivity["panel"] = {
                "status": "error",
                "error": "SOCKS5 proxy not available"
            }
    else:
        connectivity["tunnel"] = {"status": "unknown"}
        connectivity["panel"] = {"status": "unknown"}
    
    # چک subscription endpoint
    sub_url = f"https://{SUB_DOMAIN}{SUB_PATH}"
    connectivity["sub_endpoint"] = await check_connectivity(sub_url, timeout=3)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "mode": mode,
        "services": services,
        "connectivity": connectivity,
        "config": {
            "panel_url": PANEL_URL,
            "sub_domain": SUB_DOMAIN,
            "sub_path": SUB_PATH,
        },
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.get("/api/status")
async def api_status():
    """API برای گرفتن وضعیت به صورت JSON"""
    
    load_dotenv(CONFIG_PATH, override=True)
    mode = os.getenv("ACTIVE_MODE", "unknown")
    
    result = {
        "mode": mode,
        "timestamp": datetime.now().isoformat(),
        "services": {},
        "connectivity": {}
    }
    
    # سرویس‌ها
    result["services"]["haproxy"] = check_service_status("haproxy")
    
    if mode == "wireguard":
        result["services"]["wireguard"] = check_service_status("wg-quick@wg0")
        result["connectivity"]["tunnel"] = check_wireguard_status()
    elif mode == "xray":
        result["services"]["xray"] = check_service_status("xray-client")
        result["services"]["nginx"] = check_service_status("nginx")
        result["connectivity"]["tunnel"] = check_xray_socks()
    
    # اتصالات
    result["connectivity"]["google"] = await check_connectivity("https://www.google.com", timeout=3)
    result["connectivity"]["panel"] = await check_connectivity(PANEL_URL, timeout=5)
    
    return result


@app.post("/api/switch/{mode}")
async def switch_mode(mode: str):
    """تغییر مدل از طریق API"""
    
    if mode not in ["wireguard", "xray"]:
        return {
            "success": False,
            "error": "Invalid mode. Use 'wireguard' or 'xray'"
        }
    
    try:
        result = subprocess.run(
            ["/opt/sub-relay/switch-mode.sh", mode],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Switch operation timed out"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("DASHBOARD_PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
