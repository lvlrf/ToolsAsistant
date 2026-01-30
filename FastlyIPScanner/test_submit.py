import requests
import hashlib

SERVER = "http://194.36.174.102:8080"
_k = [68, 114, 67, 111, 110, 110, 101, 99, 116, 95, 70, 97, 115, 116, 108, 121, 95, 50, 48, 50, 53, 95, 83, 101, 99, 117, 114, 101, 95, 75, 101, 121, 95, 88, 55, 57, 51]
SECRET_KEY = ''.join(chr(c) for c in _k)

print("1. Getting timestamp...")
try:
    r = requests.get(f'{SERVER}/timestamp', timeout=5)
    print(f"   Response: {r.status_code} - {r.text}")
    ts = r.json()['timestamp']
except Exception as e:
    print(f"   ERROR: {e}")
    exit()

print(f"\n2. Generating token for timestamp: {ts}")
token = hashlib.sha256(f"{ts}{SECRET_KEY}".encode()).hexdigest()
print(f"   Token: {token[:20]}...")

print("\n3. Submitting...")
payload = {
    'timestamp': ts,
    'token': token,
    'public_ip': '1.2.3.4',
    'scan_duration': 10,
    'total_successful': 0,
    'results': []
}
try:
    r = requests.post(f'{SERVER}/submit', json=payload, timeout=5)
    print(f"   Response: {r.status_code} - {r.text}")
except Exception as e:
    print(f"   ERROR: {e}")