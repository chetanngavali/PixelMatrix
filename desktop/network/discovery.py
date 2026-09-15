"""
Network Discovery Module for PixelMatrix ESP8266
Scans local subnet or queries mDNS to automatically detect the ESP8266 controller on the Wi-Fi network.
"""
import socket
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Tuple

def check_ip(ip: str, timeout: float = 0.5) -> Optional[Tuple[str, dict]]:
    """Checks if a given IP is the PixelMatrix ESP8266 by probing port 80 /api/status."""
    url = f"http://{ip}/api/status"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PixelMatrix-Discovery"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                if "deviceName" in data and "PixelMatrix" in data["deviceName"]:
                    return (ip, data)
    except Exception:
        pass
    return None

def get_local_subnet_base() -> str:
    """Detects the active IPv4 subnet prefix (e.g., '192.168.1.')."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        parts = local_ip.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{parts[2]}."
    except Exception:
        pass
    return "192.168.1."

def discover_esp(fallback_ip: str = "192.168.1.31", timeout: float = 1.0) -> Optional[str]:
    """
    Discovers the ESP8266 on the local Wi-Fi network.
    1. First checks fallback_ip.
    2. If not found, scans the local subnet concurrently.
    Returns the discovered IP or None.
    """
    # 1. Fast check fallback / last known IP
    if fallback_ip:
        res = check_ip(fallback_ip, timeout=0.8)
        if res:
            return res[0]
            
    # 2. Sweep the /24 subnet concurrently
    subnet_base = get_local_subnet_base()
    candidates = [f"{subnet_base}{i}" for i in range(1, 255) if f"{subnet_base}{i}" != fallback_ip]
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(check_ip, ip, timeout): ip for ip in candidates}
        for future in as_completed(futures):
            try:
                res = future.result()
                if res:
                    # Cancel remaining tasks
                    executor.shutdown(wait=False, cancel_futures=True)
                    return res[0]
            except Exception:
                pass
                
    return None

if __name__ == "__main__":
    print("Searching for PixelMatrix ESP8266 on local network...")
    ip = discover_esp()
    if ip:
        print(f" Found PixelMatrix at: {ip}")
    else:
        print(" ESP8266 not found.")
