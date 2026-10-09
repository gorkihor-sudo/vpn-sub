#!/usr/bin/env python3
"""
VPN Subscription & Config Generator for GitHub Pages (NEBULA GATEWAY)
Fully automated, health-checking aggregator that validates nodes before publishing.
Generates:
- sub.txt (Base64 standard subscription)
- sub (Base64 fallback)
- sub_raw.txt (Plain text links)
- clash.yaml (Clash Meta / Mihomo full configuration)
- sing-box.json (Sing-box 1.13+ configuration with FakeIP)
- nodes.json (Structured data for the Web UI)
"""

import os
import sys
import re
import json
import base64
import socket
import ssl
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 1. High-Priority Verified Anti-Censorship & Reality Nodes
VERIFIED_CORE_NODES = [
    # VLESS-Reality (DPI / TSPU immune on port 443 with TLS Vision)
    "vless://f2381f29-c724-4491-95a3-a17bd6eea47f@46.28.69.53:443?security=reality&encryption=none&pbk=MldGYzZegwydL76HI_beMlXgD-4ZyCZjIX0sBVPjphY&headerType=none&fp=chrome&type=tcp&flow=xtls-rprx-vision&sni=de2.willo.help&sid=abcd1234#%F0%9F%87%A9%F0%9F%87%AA+Germany+Reality+Dusseldorf",
    "vless://f495298f-2bdb-4fd8-9ac9-5dd33d1b482a@177.3.213.112:443?security=reality&encryption=none&pbk=W-zf_ncm9sYALF5EqvUsxqTkYGdAw-tQczT2SqwVMGE&headerType=none&fp=chrome&type=tcp&flow=xtls-rprx-vision&sni=germanz.ruletka.study&sid=ff776ff77be48b88#%F0%9F%87%A9%F0%9F%87%AA+Germany+Reality+Frankfurt",
    "vless://5be7fb02-b6a5-450f-b041-3243b98e8420@72.56.41.33:40443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=deepl.com&fp=chrome&pbk=Uvj5H9pDJP0HX2bN7NN7sCQwVCrC5N2NbKf-yuy1ikE&sid=ee33&type=tcp&headerType=none#%F0%9F%87%BA%F0%9F%87%B8+USA+Miami+Reality",
    
    # Cloudflare Anycast High-Speed TLS Nodes (Clean Edge IPs on Port 443)
    "vless://d342d11e-d424-4583-b36e-524ab1f0afa4@104.16.132.229:443?encryption=none&security=tls&sni=speed.cloudflare.com&type=ws&host=speed.cloudflare.com&path=%2F#%F0%9F%8C%90+Cloudflare+WARP+Global+1",
    "vless://d342d11e-d424-4583-b36e-524ab1f0afa4@172.67.182.111:443?encryption=none&security=tls&sni=speed.cloudflare.com&type=ws&host=speed.cloudflare.com&path=%2F#%F0%9F%8C%90+Cloudflare+WARP+Global+2",
    "vless://96b1b606-d069-42b7-a38f-a9ca3b8431e6@162.159.193.1:443?encryption=none&security=tls&sni=cloudflare.com&type=ws&host=cloudflare.com&path=%2Fvless#%F0%9F%87%BA%F0%9F%87%B8+USA+Edge+Relay",
    
    # Singapore & Japan Fast Edge
    "vless://3adac494-0eb1-4d89-a187-b2181691444d@104.21.55.229:443?encryption=none&security=tls&sni=tiny-lake-bbf1.369-766.workers.dev&type=ws&host=tiny-lake-bbf1.369-766.workers.dev&path=%2Fpyip%3DProxyIP.SG.CMLiussss.net#%F0%9F%87%B8%F0%9F%87%AC+Singapore+Fast+Edge",
    "vless://d342d11e-d424-4583-b36e-524ab1f0afa4@198.41.214.162:443?encryption=none&security=tls&sni=speed.cloudflare.com&type=ws&host=speed.cloudflare.com&path=%2F#%F0%9F%87%AF%F0%9F%87%B5+Japan+Tokyo+Edge",
    
    # Reliable Shadowsocks & Trojan
    "trojan://trojan-pwd@104.21.64.12:443?security=tls&sni=speed.cloudflare.com&type=ws&host=speed.cloudflare.com&path=%2Ftrojan#%F0%9F%9B%A1%EF%B8%8F+Protected+Trojan+Global"
]

# 2. Upstream Free Aggregator Subscriptions
SOURCES = [
    "https://raw.githubusercontent.com/barry-far/V2ray-config/main/Splitted-By-Protocol/vless.txt",
    "https://raw.githubusercontent.com/hans-thomas/v2ray-subscription/refs/heads/master/servers.txt",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    "https://raw.githubusercontent.com/ssrsub/ssr/master/v2ray",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub"
]

ISO_TO_COUNTRY = {
    'DE': ('Германия', '🇩🇪'), 'NL': ('Нидерланды', '🇳🇱'), 'US': ('США', '🇺🇸'),
    'GB': ('Великобритания', '🇬🇧'), 'UK': ('Великобритания', '🇬🇧'), 'FR': ('Франция', '🇫🇷'),
    'FI': ('Финляндия', '🇫🇮'), 'SE': ('Швеция', '🇸🇪'), 'PL': ('Польша', '🇵🇱'),
    'CH': ('Швейцария', '🇨🇭'), 'AT': ('Австрия', '🇦🇹'), 'TR': ('Турция', '🇹🇷'),
    'ES': ('Испания', '🇪🇸'), 'IT': ('Италия', '🇮🇹'), 'CA': ('Канада', '🇨🇦'),
    'JP': ('Япония', '🇯🇵'), 'SG': ('Сингапур', '🇸🇬'), 'KR': ('Корея', '🇰🇷'),
    'HK': ('Гонконг', '🇭🇰'), 'TW': ('Тайвань', '🇹🇼'), 'KZ': ('Казахстан', '🇰🇿'),
    'DK': ('Дания', '🇩🇰'), 'NO': ('Норвегия', '🇳🇴'), 'CZ': ('Чехия', '🇨🇿'),
    'BE': ('Бельгия', '🇧🇪'), 'LT': ('Литва', '🇱🇹'), 'LV': ('Латвия', '🇱🇻'),
    'EE': ('Эстония', '🇪🇪'), 'IE': ('Ирландия', '🇮🇪'), 'AU': ('Австралия', '🇦🇺'),
    'IN': ('Индия', '🇮🇳'), 'BR': ('Бразилия', '🇧🇷'), 'RO': ('Румыния', '🇷🇴'),
    'UA': ('Украина', '🇺🇦'), 'MD': ('Молдова', '🇲🇩'), 'RS': ('Сербия', '🇷🇸'),
    'IL': ('Израиль', '🇮🇱'), 'PT': ('Португалия', '🇵🇹'), 'GR': ('Греция', '🇬🇷'),
    'HU': ('Венгрия', '🇭🇺'), 'BG': ('Болгария', '🇧🇬'), 'IS': ('Исландия', '🇮🇸'),
    'AE': ('ОАЭ', '🇦🇪'), 'CY': ('Кипр', '🇨🇾'), 'AM': ('Армения', '🇦🇲'),
    'GE': ('Грузия', '🇬🇪'), 'UZ': ('Узбекистан', '🇺🇿')
}

NAME_KEYWORDS = {
    'де': 'DE', 'герман': 'DE', 'germany': 'DE', 'frankfurt': 'DE', 'berlin': 'DE', 'dusseldorf': 'DE', 'deu': 'DE',
    'нидерланд': 'NL', 'netherlands': 'NL', 'holland': 'NL', 'amsterdam': 'NL', 'nld': 'NL',
    'сша': 'US', 'usa': 'US', 'united states': 'US', 'america': 'US', 'new york': 'US', 'miami': 'US', 'los angeles': 'US',
    'великобрит': 'GB', 'united kingdom': 'GB', 'england': 'GB', 'london': 'GB', 'gbr': 'GB',
    'франц': 'FR', 'france': 'FR', 'paris': 'FR', 'fra': 'FR',
    'финлянд': 'FI', 'finland': 'FI', 'helsinki': 'FI', 'fin': 'FI',
    'швеци': 'SE', 'sweden': 'SE', 'stockholm': 'SE', 'swe': 'SE',
    'польш': 'PL', 'poland': 'PL', 'warsaw': 'PL', 'pol': 'PL',
    'швейцар': 'CH', 'switzerland': 'CH', 'zurich': 'CH', 'che': 'CH',
    'австри': 'AT', 'austria': 'AT', 'vienna': 'AT', 'aut': 'AT',
    'турци': 'TR', 'turkey': 'TR', 'istanbul': 'TR', 'tur': 'TR',
    'испан': 'ES', 'spain': 'ES', 'madrid': 'ES', 'esp': 'ES',
    'итали': 'IT', 'italy': 'IT', 'milan': 'IT', 'rome': 'IT', 'ita': 'IT',
    'канад': 'CA', 'canada': 'CA', 'toronto': 'CA', 'can': 'CA',
    'япон': 'JP', 'japan': 'JP', 'tokyo': 'JP', 'jpn': 'JP',
    'сингапур': 'SG', 'singapore': 'SG', 'sgp': 'SG',
    'коре': 'KR', 'korea': 'KR', 'seoul': 'KR', 'kor': 'KR',
    'гонконг': 'HK', 'hong kong': 'HK', 'hkg': 'HK',
    'тайван': 'TW', 'taiwan': 'TW', 'twn': 'TW',
    'казахстан': 'KZ', 'kazakhstan': 'KZ', 'almaty': 'KZ', 'kaz': 'KZ',
    'дани': 'DK', 'denmark': 'DK', 'copenhagen': 'DK', 'dnk': 'DK',
    'норвег': 'NO', 'norway': 'NO', 'oslo': 'NO', 'nor': 'NO',
    'бельги': 'BE', 'belgium': 'BE', 'brussels': 'BE', 'bel': 'BE',
    'литв': 'LT', 'lithuania': 'LT', 'vilnius': 'LT', 'ltu': 'LT',
    'латви': 'LV', 'latvia': 'LV', 'riga': 'LV', 'lva': 'LV',
    'эстони': 'EE', 'estonia': 'EE', 'tallinn': 'EE', 'est': 'EE',
    'ирланд': 'IE', 'ireland': 'IE', 'dublin': 'IE', 'irl': 'IE',
    'чехи': 'CZ', 'czech': 'CZ', 'prague': 'CZ', 'cze': 'CZ',
    'румыни': 'RO', 'romania': 'RO', 'bucharest': 'RO', 'rou': 'RO',
    'украин': 'UA', 'ukraine': 'UA', 'kyiv': 'UA', 'ukr': 'UA',
    'молдов': 'MD', 'moldova': 'MD', 'chisinau': 'MD', 'mda': 'MD',
    'серби': 'RS', 'serbia': 'RS', 'belgrade': 'RS', 'srb': 'RS',
    'австрали': 'AU', 'australia': 'AU', 'sydney': 'AU', 'aus': 'AU',
    'инди': 'IN', 'india': 'IN', 'mumbai': 'IN', 'ind': 'IN',
    'бразили': 'BR', 'brazil': 'BR', 'bra': 'BR',
    'израиль': 'IL', 'israel': 'IL', 'tel aviv': 'IL', 'isr': 'IL'
}

def detect_country(name: str, host: str):
    # 1. First priority: decode Unicode Regional Indicator Symbol emoji flags (e.g. 🇩🇰, 🇳🇱, 🇩🇪)
    for i in range(len(name) - 1):
        c1, c2 = ord(name[i]), ord(name[i+1])
        if 0x1F1E6 <= c1 <= 0x1F1FF and 0x1F1E6 <= c2 <= 0x1F1FF:
            code = chr(ord('A') + c1 - 0x1F1E6) + chr(ord('A') + c2 - 0x1F1E6)
            if code in ISO_TO_COUNTRY:
                return ISO_TO_COUNTRY[code]
                
    # 2. Clean out ad domains that cause false positives (e.g. dafei.de)
    cleaned = re.sub(r'dafei\.de|v2nodes\.com', '', (name + ' ' + host).lower())
    
    # 3. Keyword matching (Russian, English, 3-letter ISO)
    for kw, code in NAME_KEYWORDS.items():
        pattern = r'(?:\b|_|-)' + re.escape(kw) + r'(?:\b|_|-|\d)'
        if re.search(pattern, cleaned) or kw in cleaned:
            return ISO_TO_COUNTRY[code]
            
    # 4. Two-letter country code check
    for code, (country, flag) in ISO_TO_COUNTRY.items():
        if re.search(r'\b' + code.lower() + r'\b', cleaned):
            return country, flag
            
    return "Глобальный", "🌐"

def clean_tag(raw: str, fallback="VPN Node") -> str:
    if not raw:
        return fallback
    try:
        t = urllib.parse.unquote(raw).replace("+", " ").strip()
        return t or fallback
    except Exception:
        return raw or fallback

def fetch_source(url: str):
    print(f"Fetching upstream: {url}")
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "v2rayNG/1.8.5 (Windows NT 10.0; Win64; x64)",
                "Accept": "*/*"
            }
        )
        with urllib.request.urlopen(req, timeout=8) as res:
            raw = res.read().strip()
            text = raw.decode("utf-8", errors="ignore")
            if "://" in text:
                lines = text.splitlines()
            else:
                try:
                    clean_b64 = re.sub(r'[\r\n\s]', '', text)
                    clean_b64 += "=" * ((4 - len(clean_b64) % 4) % 4)
                    decoded = base64.b64decode(clean_b64).decode("utf-8", errors="ignore")
                    lines = decoded.splitlines()
                except Exception:
                    lines = text.splitlines()
            return [l.strip() for l in lines if l.strip()]
    except Exception as e:
        print(f"  Warning: failed {url}: {e}")
        return []

def parse_node(link: str):
    link = link.strip()
    if not link:
        return None
    try:
        if link.startswith("vless://"):
            parsed = urllib.parse.urlparse(link)
            query = urllib.parse.parse_qs(parsed.query)
            tag = clean_tag(parsed.fragment, "VLESS Node")
            host = parsed.hostname or ""
            port = parsed.port or 443
            uuid = parsed.username or ""
            security = query.get("security", ["none"])[0].lower()
            is_reality = security == "reality"
            is_tls = security in ("tls", "reality")
            flow = query.get("flow", [""])[0]
            net_type = query.get("type", ["tcp"])[0].lower()
            sni = query.get("sni", [host])[0]
            ws_host = query.get("host", [sni])[0]
            ws_path = query.get("path", ["/"])[0]
            pbk = query.get("pbk", [""])[0]
            sid = query.get("sid", [""])[0]
            fp = query.get("fp", ["chrome"])[0]
            country, flag = detect_country(tag, host)
            
            return {
                "raw": link,
                "protocol": "VLESS",
                "name": tag,
                "host": host,
                "port": port,
                "uuid": uuid,
                "country": country,
                "flag": flag,
                "security": "Reality" if is_reality else ("TLS" if is_tls else "None"),
                "is_reality": is_reality,
                "is_tls": is_tls,
                "flow": flow,
                "type": net_type,
                "sni": sni,
                "ws_host": ws_host,
                "ws_path": ws_path,
                "pbk": pbk,
                "sid": sid,
                "fp": fp
            }
            
        elif link.startswith("vmess://"):
            payload = link[8:]
            payload += "=" * ((4 - len(payload) % 4) % 4)
            data = json.loads(base64.b64decode(payload).decode("utf-8", errors="ignore"))
            tag = clean_tag(data.get("ps", "VMess Node"))
            host = data.get("add", "")
            port = int(data.get("port", 443))
            country, flag = detect_country(tag, host)
            is_tls = str(data.get("tls", "")).lower() == "tls"
            
            return {
                "raw": link,
                "protocol": "VMess",
                "name": tag,
                "host": host,
                "port": port,
                "uuid": data.get("id", ""),
                "country": country,
                "flag": flag,
                "security": "TLS" if is_tls else "None",
                "is_reality": False,
                "is_tls": is_tls,
                "flow": "",
                "type": data.get("net", "tcp"),
                "sni": data.get("sni") or data.get("host") or host,
                "ws_host": data.get("host") or host,
                "ws_path": data.get("path", "/"),
                "cipher": data.get("scy", "auto"),
                "alterId": int(data.get("aid", 0))
            }
            
        elif link.startswith("trojan://"):
            parsed = urllib.parse.urlparse(link)
            query = urllib.parse.parse_qs(parsed.query)
            tag = clean_tag(parsed.fragment, "Trojan Node")
            host = parsed.hostname or ""
            port = parsed.port or 443
            password = parsed.username or ""
            country, flag = detect_country(tag, host)
            sni = query.get("sni", [host])[0]
            ws_host = query.get("host", [sni])[0]
            ws_path = query.get("path", ["/"])[0]
            net_type = query.get("type", ["tcp"])[0].lower()
            
            return {
                "raw": link,
                "protocol": "Trojan",
                "name": tag,
                "host": host,
                "port": port,
                "password": password,
                "country": country,
                "flag": flag,
                "security": "TLS",
                "is_reality": False,
                "is_tls": True,
                "flow": "",
                "type": net_type,
                "sni": sni,
                "ws_host": ws_host,
                "ws_path": ws_path
            }
            
        elif link.startswith("ss://"):
            tag = "Shadowsocks Node"
            clean_link = link
            if "#" in link:
                parts = link.split("#", 1)
                clean_link = parts[0]
                tag = clean_tag(parts[1], "Shadowsocks Node")
            
            body = clean_link.replace("ss://", "")
            host = ""
            port = 8388
            method = "chacha20-ietf-poly1305"
            password = ""
            
            if "@" in body:
                userinfo_b64, host_port = body.split("@", 1)
                try:
                    userinfo_b64 += "=" * ((4 - len(userinfo_b64) % 4) % 4)
                    decoded = base64.b64decode(userinfo_b64).decode("utf-8")
                    method, password = decoded.split(":", 1)
                except Exception:
                    pass
                if ":" in host_port:
                    h, p = host_port.split(":", 1)
                    host = h
                    port = int(p)
            else:
                try:
                    body += "=" * ((4 - len(body) % 4) % 4)
                    decoded = base64.b64decode(body).decode("utf-8")
                    m = re.match(r"^([^:]+):([^@]+)@([^:]+):(\d+)$", decoded)
                    if m:
                        method, password, host, port_str = m.groups()
                        port = int(port_str)
                except Exception:
                    pass
                    
            if not host:
                return None
                
            country, flag = detect_country(tag, host)
            return {
                "raw": link,
                "protocol": "Shadowsocks",
                "name": tag,
                "host": host,
                "port": port,
                "cipher": method,
                "password": password,
                "country": country,
                "flag": flag,
                "security": "Standard",
                "is_reality": False,
                "is_tls": False,
                "flow": "",
                "type": "tcp"
            }
    except Exception:
        return None
    return None

def check_node_health(node: dict, timeout=2.5) -> dict:
    """
    Validates genuine network responsiveness and measures TCP/TLS RTT.
    Filters out dead servers and unreachable hosts.
    """
    host = node.get("host")
    port = node.get("port")
    if not host or not port or port <= 0 or port > 65535:
        return None
        
    # Exclude known broken / dead servers
    EXCLUDED_HOSTS = ["45.130.125.158", "render.com", "www.darkroom.lol"]
    if host in EXCLUDED_HOSTS or node.get("sni") == "www.ignitelimit.com":
        return None
        
    # Drop plain unencrypted port 8080 (blocked by Russian TSPU/DPI)
    if port == 8080 and not node.get("is_tls") and not node.get("is_reality"):
        return None

    start = time.time()
    try:
        # 1. Resolve host
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        # 2. Measure TCP connect
        t0 = time.time()
        sock.connect((host, port))
        tcp_ms = int((time.time() - t0) * 1000)
        
        # 3. If TLS / Reality, test TLS Handshake
        if node.get("is_tls") or node.get("is_reality"):
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            sni = node.get("sni") or host
            ssock = context.wrap_socket(sock, server_hostname=sni)
            ssock.settimeout(timeout)
            tls_ms = int((time.time() - t0) * 1000)
            ssock.close()
            latency = tls_ms
        else:
            sock.close()
            latency = tcp_ms
            
        node["ping"] = max(15, latency)
        node["status"] = "online"
        return node
    except Exception:
        return None

def build_clash_yaml(nodes):
    proxies = []
    proxy_names = []
    
    for i, n in enumerate(nodes):
        name = f"{n['flag']} {n['country']} #{i+1} [{n['security']}]"
        proxy_names.append(f'"{name}"')
        
        proto = n["protocol"].lower()
        if proto == "vless":
            proxy_dict = {
                "name": name,
                "type": "vless",
                "server": n["host"],
                "port": n["port"],
                "uuid": n.get("uuid", ""),
                "udp": True,
                "tls": n.get("is_tls", False),
                "skip-cert-verify": True,
                "network": n.get("type", "tcp")
            }
            if n.get("flow"):
                proxy_dict["flow"] = n["flow"]
            if n.get("sni"):
                proxy_dict["servername"] = n["sni"]
            if n.get("is_reality"):
                proxy_dict["reality-opts"] = {
                    "public-key": n.get("pbk", ""),
                    "short-id": n.get("sid", "")
                }
                proxy_dict["client-fingerprint"] = n.get("fp", "chrome")
            if n.get("type") == "ws":
                proxy_dict["ws-opts"] = {
                    "path": n.get("ws_path", "/"),
                    "headers": {"Host": n.get("ws_host", n["host"])}
                }
            proxies.append(proxy_dict)
            
        elif proto == "vmess":
            proxy_dict = {
                "name": name,
                "type": "vmess",
                "server": n["host"],
                "port": n["port"],
                "uuid": n.get("uuid", ""),
                "alterId": n.get("alterId", 0),
                "cipher": n.get("cipher", "auto"),
                "udp": True,
                "tls": n.get("is_tls", False),
                "skip-cert-verify": True,
                "network": n.get("type", "tcp")
            }
            if n.get("sni"):
                proxy_dict["servername"] = n["sni"]
            if n.get("type") == "ws":
                proxy_dict["ws-opts"] = {
                    "path": n.get("ws_path", "/"),
                    "headers": {"Host": n.get("ws_host", n["host"])}
                }
            proxies.append(proxy_dict)
            
        elif proto == "trojan":
            proxy_dict = {
                "name": name,
                "type": "trojan",
                "server": n["host"],
                "port": n["port"],
                "password": n.get("password", ""),
                "udp": True,
                "sni": n.get("sni", n["host"]),
                "skip-cert-verify": True,
                "network": n.get("type", "tcp")
            }
            if n.get("type") == "ws":
                proxy_dict["ws-opts"] = {
                    "path": n.get("ws_path", "/"),
                    "headers": {"Host": n.get("ws_host", n["host"])}
                }
            proxies.append(proxy_dict)
            
        elif proto == "shadowsocks":
            proxies.append({
                "name": name,
                "type": "ss",
                "server": n["host"],
                "port": n["port"],
                "cipher": n.get("cipher", "chacha20-ietf-poly1305"),
                "password": n.get("password", ""),
                "udp": True
            })

    # Convert to valid clean YAML
    lines = [
        "# Nebula / GorkiVPN Clash Meta & Mihomo Configuration",
        f"# Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "port: 7890",
        "socks-port: 7891",
        "allow-lan: false",
        "mode: rule",
        "log-level: info",
        "ipv6: false",
        "",
        "dns:",
        "  enable: true",
        "  enhanced-mode: fake-ip",
        "  fake-ip-range: 198.18.0.1/16",
        "  nameserver:",
        "    - 1.1.1.1",
        "    - 8.8.8.8",
        "    - https://dns.cloudflare.com/dns-query",
        "",
        "proxies:"
    ]
    
    for p in proxies:
        lines.append(f"  - name: \"{p['name']}\"")
        lines.append(f"    type: {p['type']}")
        lines.append(f"    server: \"{p['server']}\"")
        lines.append(f"    port: {p['port']}")
        if "uuid" in p:
            lines.append(f"    uuid: \"{p['uuid']}\"")
        if "password" in p:
            lines.append(f"    password: \"{p['password']}\"")
        if "cipher" in p:
            lines.append(f"    cipher: \"{p['cipher']}\"")
        if "alterId" in p:
            lines.append(f"    alterId: {p['alterId']}")
        if "tls" in p:
            lines.append(f"    tls: {str(p['tls']).lower()}")
            lines.append("    skip-cert-verify: true")
        if "flow" in p:
            lines.append(f"    flow: \"{p['flow']}\"")
        if "servername" in p:
            lines.append(f"    servername: \"{p['servername']}\"")
        if "client-fingerprint" in p:
            lines.append(f"    client-fingerprint: \"{p['client-fingerprint']}\"")
        if "reality-opts" in p:
            lines.append("    reality-opts:")
            lines.append(f"      public-key: \"{p['reality-opts']['public-key']}\"")
            lines.append(f"      short-id: \"{p['reality-opts']['short-id']}\"")
        if "network" in p and p["network"] == "ws":
            lines.append("    network: ws")
            lines.append("    ws-opts:")
            lines.append(f"      path: \"{p['ws-opts']['path']}\"")
            lines.append("      headers:")
            lines.append(f"        Host: \"{p['ws-opts']['headers']['Host']}\"")
        lines.append("    udp: true")
        lines.append("")

    lines.extend([
        "proxy-groups:",
        "  - name: \"⚡ Auto Best Latency\"",
        "    type: url-test",
        "    url: http://cp.cloudflare.com/generate_204",
        "    interval: 300",
        "    tolerance: 50",
        "    proxies:",
        *[f"      - {pname}" for pname in proxy_names],
        "",
        "  - name: \"🚀 Select Proxy\"",
        "    type: select",
        "    proxies:",
        "      - \"⚡ Auto Best Latency\"",
        *[f"      - {pname}" for pname in proxy_names],
        "      - DIRECT",
        "",
        "rules:",
        "  - DOMAIN-SUFFIX,local,DIRECT",
        "  - IP-CIDR,127.0.0.0/8,DIRECT",
        "  - IP-CIDR,192.168.0.0/16,DIRECT",
        "  - IP-CIDR,10.0.0.0/8,DIRECT",
        "  - GEOIP,LAN,DIRECT",
        "  - MATCH,\"🚀 Select Proxy\"",
        ""
    ])
    
    return "\n".join(lines)

def build_sing_box_json(nodes):
    outbounds = [
        {
            "type": "selector",
            "tag": "select",
            "outbounds": ["auto"] + [f"node-{i}" for i in range(len(nodes))] + ["direct"]
        },
        {
            "type": "urltest",
            "tag": "auto",
            "outbounds": [f"node-{i}" for i in range(len(nodes))],
            "url": "http://cp.cloudflare.com/generate_204",
            "interval": "3m"
        },
        {"type": "direct", "tag": "direct"}
    ]
    
    for i, n in enumerate(nodes):
        proto = n["protocol"].lower()
        ob = {
            "type": proto,
            "tag": f"node-{i}",
            "server": n["host"],
            "server_port": n["port"]
        }
        if proto == "vless":
            ob["uuid"] = n.get("uuid", "")
            if n.get("flow"):
                ob["flow"] = n["flow"]
            if n.get("is_tls") or n.get("is_reality"):
                ob["tls"] = {
                    "enabled": True,
                    "server_name": n.get("sni", n["host"]),
                    "insecure": True
                }
                if n.get("is_reality"):
                    ob["tls"]["reality"] = {
                        "enabled": True,
                        "public_key": n.get("pbk", ""),
                        "short_id": n.get("sid", "")
                    }
                    ob["tls"]["utls"] = {
                        "enabled": True,
                        "fingerprint": n.get("fp", "chrome")
                    }
            if n.get("type") == "ws":
                ob["transport"] = {
                    "type": "ws",
                    "path": n.get("ws_path", "/"),
                    "headers": {"Host": n.get("ws_host", n["host"])}
                }
        elif proto == "vmess":
            ob["uuid"] = n.get("uuid", "")
            ob["security"] = n.get("cipher", "auto")
            ob["alter_id"] = n.get("alterId", 0)
            if n.get("is_tls"):
                ob["tls"] = {"enabled": True, "server_name": n.get("sni", n["host"]), "insecure": True}
            if n.get("type") == "ws":
                ob["transport"] = {
                    "type": "ws",
                    "path": n.get("ws_path", "/"),
                    "headers": {"Host": n.get("ws_host", n["host"])}
                }
        elif proto == "trojan":
            ob["password"] = n.get("password", "")
            ob["tls"] = {"enabled": True, "server_name": n.get("sni", n["host"]), "insecure": True}
            if n.get("type") == "ws":
                ob["transport"] = {
                    "type": "ws",
                    "path": n.get("ws_path", "/"),
                    "headers": {"Host": n.get("ws_host", n["host"])}
                }
        elif proto == "shadowsocks":
            ob["method"] = n.get("cipher", "chacha20-ietf-poly1305")
            ob["password"] = n.get("password", "")
            
        outbounds.append(ob)
        
    cfg = {
        "log": {"level": "warn", "timestamp": True},
        "dns": {
            "servers": [
                {"tag": "fakeip", "type": "fakeip", "inet4_range": "198.18.0.0/15"},
                {"tag": "remote", "type": "https", "server": "8.8.8.8", "detour": "select"},
                {"tag": "local", "type": "local"}
            ],
            "rules": [
                {"query_type": ["HTTPS"], "action": "reject"},
                {"query_type": ["A", "AAAA"], "server": "fakeip"}
            ],
            "final": "local"
        },
        "inbounds": [
            {
                "type": "tun",
                "tag": "tun-in",
                "address": ["172.19.0.1/30"],
                "mtu": 9000,
                "auto_route": True,
                "strict_route": False,
                "stack": "mixed"
            }
        ],
        "outbounds": outbounds,
        "route": {
            "auto_detect_interface": True,
            "default_domain_resolver": {"server": "local", "strategy": "ipv4_only"},
            "final": "select",
            "rules": [
                {"port": 53, "action": "hijack-dns"},
                {"ip_is_private": True, "outbound": "direct"}
            ]
        }
    }
    return json.dumps(cfg, indent=2, ensure_ascii=False)

def enrich_nodes_geoip(nodes):
    print("Enriching node geo-locations with IP GeoIP batch lookup...")
    host_to_ip = {}
    for n in nodes:
        h = n.get("host")
        if h and h not in host_to_ip:
            try:
                host_to_ip[h] = socket.gethostbyname(h)
            except Exception:
                host_to_ip[h] = h

    unique_ips = list(set(host_to_ip.values()))
    ip_geo = {}
    
    # Query in batches of 30
    chunk_size = 30
    for i in range(0, len(unique_ips), chunk_size):
        chunk = unique_ips[i:i + chunk_size]
        payload = [{"query": ip, "fields": "query,country,countryCode,city"} for ip in chunk]
        try:
            req = urllib.request.Request(
                "http://ip-api.com/batch",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                for item in data:
                    ip = item.get("query")
                    if ip:
                        ip_geo[ip] = item
        except Exception as e:
            print(f"  GeoIP notice: {e}")

    for n in nodes:
        h = n.get("host")
        ip = host_to_ip.get(h, h)
        geo = ip_geo.get(ip)
        if geo:
            code = geo.get("countryCode", "")
            if code in ISO_TO_COUNTRY:
                c_name, c_flag = ISO_TO_COUNTRY[code]
                n["country"] = c_name
                n["flag"] = c_flag
                n["city"] = geo.get("city") or ""
        if "city" not in n:
            n["city"] = ""

def main():
    print("=== [NEBULA GATEWAY] Starting VPN Node Verification & Aggregation ===")
    all_raw = list(VERIFIED_CORE_NODES)
    
    # Fetch from upstream
    for src in SOURCES:
        links = fetch_source(src)
        all_raw.extend(links)
        
    # Deduplicate raw links & prioritize Reality and distinct hosts
    seen = set()
    core_candidates = []
    reality_candidates = []
    other_candidates = []
    
    for link in all_raw:
        link = link.strip()
        if not link.startswith(("vless://", "vmess://", "trojan://", "ss://")):
            continue
        base = link.split("#")[0]
        if base in seen:
            continue
        seen.add(base)
        if link in VERIFIED_CORE_NODES:
            core_candidates.append(link)
        elif "security=reality" in link:
            reality_candidates.append(link)
        else:
            other_candidates.append(link)
            
    # Sample up to 300 reality and 100 other candidate nodes across different hosts
    candidate_links = core_candidates + reality_candidates[:300] + other_candidates[:100]
    print(f"Selected {len(candidate_links)} prioritized candidate nodes to test ({len(core_candidates)} core, {min(300, len(reality_candidates))} reality, {min(100, len(other_candidates))} others)")
    
    # Parse candidates
    parsed_candidates = []
    for l in candidate_links:
        p = parse_node(l)
        if p and p.get("host"):
            parsed_candidates.append(p)
            
    print(f"Parsed {len(parsed_candidates)} valid candidate nodes. Starting live health test...")
    
    # Concurrent health check (test TCP/TLS response)
    verified_nodes = []
    with ThreadPoolExecutor(max_workers=35) as executor:
        futures = {executor.submit(check_node_health, n): n for n in parsed_candidates}
        for future in as_completed(futures):
            res = future.result()
            if res:
                verified_nodes.append(res)
                
    print(f"\nHealth check finished: {len(verified_nodes)}/{len(parsed_candidates)} nodes online.")
    
    # Enrich with GeoIP data for precise countries and cities
    enrich_nodes_geoip(verified_nodes)
    
    # Format clean titles with country flags, country names, city, and protocol tags
    country_counters = {}
    for n in verified_nodes:
        c = n["country"]
        country_counters[c] = country_counters.get(c, 0) + 1
        idx = country_counters[c]
        city_str = f" | {n['city']}" if n.get("city") else ""
        sec_str = " [Reality]" if n.get("is_reality") else f" [{n['protocol']}]"
        clean_title = f"{n['flag']} {n['country']}{city_str}{sec_str} #{idx}"
        n["name"] = clean_title
        base_link = n["raw"].split("#")[0]
        n["raw"] = f"{base_link}#{urllib.parse.quote(clean_title)}"
        
    # Group verified nodes by country for round-robin diversity
    by_country = {}
    for n in verified_nodes:
        c = n["country"]
        if c not in by_country:
            by_country[c] = []
        by_country[c].append(n)
        
    for c in by_country:
        by_country[c].sort(key=lambda x: (0 if x.get("is_reality") else 1, x.get("ping", 9999)))
        
    interleaved_nodes = []
    max_count = max(len(v) for v in by_country.values()) if by_country else 0
    # Put top 1 from each country first, then top 2 from each country, etc.
    for round_idx in range(max_count):
        for c in sorted(by_country.keys()):
            if round_idx < len(by_country[c]):
                interleaved_nodes.append(by_country[c][round_idx])
                
    clean_links = [n["raw"] for n in interleaved_nodes]
    top_curated = interleaved_nodes[:80]
    
    # 1. sub_raw.txt
    with open("sub_raw.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(clean_links) + "\n")
        
    # 2. sub.txt (Base64 standard format)
    b64_content = base64.b64encode("\n".join(clean_links).encode("utf-8")).decode("utf-8")
    with open("sub.txt", "w", encoding="utf-8") as f:
        f.write(b64_content)
        
    with open("sub", "w", encoding="utf-8") as f:
        f.write(b64_content)
        
    # 3. nodes.json (For Web Portal UI)
    nodes_summary = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_nodes": len(verified_nodes),
        "total_countries": len(by_country),
        "avg_ping": int(sum(n["ping"] for n in top_curated) / max(1, len(top_curated))),
        "protocols": {
            "vless": sum(1 for n in verified_nodes if n["protocol"] == "VLESS"),
            "reality": sum(1 for n in verified_nodes if n.get("is_reality")),
            "vmess": sum(1 for n in verified_nodes if n["protocol"] == "VMess"),
            "trojan": sum(1 for n in verified_nodes if n["protocol"] == "Trojan"),
            "shadowsocks": sum(1 for n in verified_nodes if n["protocol"] == "Shadowsocks")
        },
        "countries": {c: len(nodes) for c, nodes in sorted(by_country.items(), key=lambda x: -len(x[1]))},
        "nodes": top_curated
    }
    with open("nodes.json", "w", encoding="utf-8") as f:
        json.dump(nodes_summary, f, indent=2, ensure_ascii=False)
        
    # 4. clash.yaml (Clash Meta / Mihomo configuration with top 60 curated nodes)
    clash_content = build_clash_yaml(top_curated)
    with open("clash.yaml", "w", encoding="utf-8") as f:
        f.write(clash_content)
        
    # 5. sing-box.json (Sing-box 1.13+ config with FakeIP and top 60 curated nodes)
    sing_box_content = build_sing_box_json(top_curated)
    with open("sing-box.json", "w", encoding="utf-8") as f:
        f.write(sing_box_content)
        
    print("\nSUCCESS: All subscription and config files generated with 100% verified online nodes!")

if __name__ == "__main__":
    main()
