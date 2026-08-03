from fastapi import APIRouter, HTTPException, Request
from schemas.internet_tools import *
import urllib.parse
import json
import base64
import requests
import dns.resolver
import ping3
import speedtest
import pyshorteners
import time
import socket

router = APIRouter(prefix="/internet-tools", tags=["Internet Tools"])

@router.post("/url/shorten", response_model=URLShortenResponse)
def shorten_url(req: URLShortenRequest):
    try:
        s = pyshorteners.Shortener()
        short_url = None
        
        methods = [
            s.tinyurl.short,
            s.isgd.short,
            s.dagd.short,
            s.clckru.short,
            s.osdb.short
        ]
        
        for method in methods:
            try:
                result = method(str(req.url))
                if result and result.startswith("http"):
                    short_url = result
                    break
            except Exception:
                continue
                
        if not short_url:
            raise Exception("All URL shortening services failed or returned invalid responses.")
            
        return {"short_url": short_url, "original_url": str(req.url)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to shorten URL: {str(e)}")

@router.post("/url/expand")
def expand_url(req: URLExpandRequest):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        try:
            response = requests.head(str(req.short_url), allow_redirects=True, timeout=10, headers=headers)
            if response.status_code >= 400:
                response = requests.get(str(req.short_url), allow_redirects=True, timeout=10, headers=headers)
        except Exception:
            response = requests.get(str(req.short_url), allow_redirects=True, timeout=10, headers=headers)
            
        return {"expanded_url": str(response.url), "original_url": str(req.short_url)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to expand URL: {str(e)}")

@router.post("/link/check")
def check_link(req: LinkCheckRequest):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(str(req.url), timeout=10, headers=headers)
        is_safe = str(req.url).startswith("https://")
        return {
            "url": str(req.url),
            "status_code": response.status_code,
            "is_up": response.status_code < 400,
            "is_https": is_safe
        }
    except Exception as e:
        is_safe = str(req.url).startswith("https://")
        return {
            "url": str(req.url),
            "status_code": 0,
            "is_up": False,
            "is_https": is_safe,
            "error": str(e)
        }

@router.post("/email/validate")
def validate_email(req: EmailValidateRequest):
    try:
        domain = req.email.split("@")[1]
        try:
            records = dns.resolver.resolve(domain, 'MX')
            mx_records = [str(r.exchange) for r in records]
            is_valid = len(mx_records) > 0
        except Exception:
            is_valid = False
            mx_records = []
            
        return {
            "email": req.email,
            "is_valid_format": True,
            "has_mx_records": is_valid,
            "mx_records": mx_records
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

import geoip2.database
from playwright.async_api import async_playwright
import os

@router.get("/ip/lookup")
def ip_lookup(request: Request, ip: Optional[str] = None):
    target_ip = ip or request.client.host
    try:
        response = requests.get(f"http://ip-api.com/json/{target_ip}", timeout=10)
        data = response.json()
        if data.get("status") == "success":
            return {
                "ip": target_ip,
                "country": data.get("country", "N/A"),
                "city": data.get("city", "N/A"),
                "latitude": data.get("lat", "N/A"),
                "longitude": data.get("lon", "N/A")
            }
        else:
            return {"ip": target_ip, "message": f"Could not find location for IP: {target_ip}"}
    except Exception as e:
        return {"ip": target_ip, "message": f"IP lookup failed: {str(e)}"}

@router.post("/website/status")
def website_status(req: StatusCheckRequest):
    try:
        start_time = time.time()
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(str(req.url), timeout=10, headers=headers)
        elapsed = round((time.time() - start_time) * 1000, 2)
        return {
            "url": str(req.url),
            "status_code": response.status_code,
            "is_up": response.status_code < 400,
            "response_time_ms": elapsed
        }
    except Exception as e:
        return {"url": str(req.url), "is_up": False, "error": str(e)}

@router.post("/dns/lookup")
def dns_lookup(req: DNSLookupRequest):
    records = {}
    for record_type in ['A', 'MX', 'TXT', 'NS']:
        try:
            answers = dns.resolver.resolve(req.domain, record_type)
            records[record_type] = [str(r) for r in answers]
        except Exception:
            records[record_type] = []
    return {"domain": req.domain, "records": records}

@router.post("/ping")
def ping_test(req: PingRequest):
    try:
        latency = ping3.ping(req.host, timeout=2)
        if latency is None:
            return {"host": req.host, "is_reachable": False}
        return {"host": req.host, "is_reachable": True, "latency_ms": round(latency * 1000, 2)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/speedtest")
def run_speedtest():
    try:
        st = speedtest.Speedtest(secure=True)
        st.get_best_server()
        download_speed = st.download() / 1_000_000 # Mbps
        upload_speed = st.upload() / 1_000_000 # Mbps
        
        # speedtest-cli ping is bugged on some environments returning massive numbers
        # We'll use ping3 to ping a reliable public DNS (8.8.8.8) for true internet latency
        import ping3
        real_ping = ping3.ping('8.8.8.8', timeout=2)
        if real_ping is not None:
            final_ping = real_ping * 1000
        else:
            final_ping = st.results.ping

        return {
            "download_mbps": round(download_speed, 2),
            "upload_mbps": round(upload_speed, 2),
            "ping_ms": round(final_ping, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Speedtest failed: {str(e)}")

@router.post("/json/format")
def format_json(req: JSONFormatRequest):
    try:
        parsed = json.loads(req.json_string)
        formatted = json.dumps(parsed, indent=4)
        return {"is_valid": True, "formatted_json": formatted}
    except Exception as e:
        return {"is_valid": False, "error": str(e)}

@router.post("/base64/process")
def process_base64(req: Base64ProcessRequest):
    try:
        if req.action.lower() == "encode":
            encoded = base64.b64encode(req.text.encode('utf-8')).decode('utf-8')
            return {"result": encoded}
        elif req.action.lower() == "decode":
            decoded = base64.b64decode(req.text.encode('utf-8')).decode('utf-8')
            return {"result": decoded}
        else:
            raise ValueError("Action must be 'encode' or 'decode'")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

from fastapi.responses import StreamingResponse
import io

@router.get("/screenshot")
async def capture_screenshot(url: str):
    try:
        if not url.startswith("http"):
            url = "http://" + url
            
        import urllib.parse
        encoded_url = urllib.parse.quote(url, safe='')
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        import time
        
        # Try WordPress mshots first (highly reliable)
        api_url = f"https://s0.wp.com/mshots/v1/{encoded_url}?w=1200"
        
        # Loop up to 3 times to wait for the image to be generated
        for _ in range(3):
            response = requests.get(api_url, headers=headers, timeout=20)
            content_type = response.headers.get("Content-Type", "")
            
            # If it's a valid JPEG/PNG and has decent size, break
            if response.status_code == 200 and "gif" not in content_type.lower() and len(response.content) > 20000:
                break
            time.sleep(3)
        
        # If mshots STILL returns a GIF or is small, fallback to thum.io
        if response.status_code != 200 or "gif" in content_type.lower() or len(response.content) < 20000:
            api_url = f"https://image.thum.io/get/width/1200/crop/1800/{url}"
            for _ in range(3):
                response = requests.get(api_url, headers=headers, timeout=20)
                # thum.io placeholders are usually < 15000 bytes
                if response.status_code == 200 and len(response.content) > 15000:
                    break
                time.sleep(3)
                
            if response.status_code != 200:
                raise Exception("Failed to capture website from both APIs.")
            content_type = response.headers.get("Content-Type", "image/jpeg")
                
        return StreamingResponse(io.BytesIO(response.content), media_type=content_type)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Screenshot failed: {str(e)}")

from fastapi.responses import StreamingResponse
from utils import generators

@router.post("/qr/wifi")
def generate_wifi_qr(req: WiFiQRRequest):
    try:
        data = generators.format_qr_data("wifi", "", {"ssid": req.ssid, "password": req.password, "encryption": req.encryption})
        buf = generators.generate_qr_code(data, fill_color=req.fill_color, back_color=req.back_color)
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/qr/upi")
def generate_upi_qr(req: UPIQRRequest):
    try:
        qr_data = {"vpa": req.vpa, "name": req.name}
        if req.amount:
            qr_data["amount"] = req.amount
        data = generators.format_qr_data("upi", "", qr_data)
        buf = generators.generate_qr_code(data, fill_color=req.fill_color, back_color=req.back_color)
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
