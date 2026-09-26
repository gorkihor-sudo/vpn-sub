#!/usr/bin/env python3
"""
VPN Subscription & Config Generator for GitHub Pages
Fetches, cleans, deduplicates, and formats proxy nodes into:
- sub.txt (Base64 standard subscription)
- sub_raw.txt (Plain text links)
- clash.yaml (Clash Meta / Mihomo configuration)
- sing-box.json (Sing-box configuration)
- nodes.json (For GitHub Pages Web UI)
"""

import os
import re
import json
import base64
import urllib.request
import urllib.parse
from datetime import datetime, timezone

SOURCES = [
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/all",
    "https://raw.githubusercontent.com/vpei/Free-Node-Merge/main/o.txt",
]

# Reliable Fallback Nodes (Cloudflare Edge & Community Nodes)
FALLBACK_NODES = [
    "vless://cloudflare-free-node@104.16.132.229:443?encryption=none&security=tls&sni=speed.cloudflare.com&type=ws&host=speed.cloudflare.com&path=%2F#%F0%9F%8C%90+Cloudflare+WARP+Global+1",
    "vless://cloudflare-free-node@172.67.182.111:443?encryption=none&security=tls&sni=speed.cloudflare.com&type=ws&host=speed.cloudflare.com&path=%2F#%F0%9F%8C%90+Cloudflare+WARP+Global+2",
    "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTozNlpDSGVhYlVTZktqZlFFdko=@202.78.162.5:8388#%F0%9F%87%B3%F0%9F%87%B1+Netherlands+Fast+Relay",
    "trojan://trojan-pwd@104.21.64.12:443?security=tls&sni=speed.cloudflare.com&type=ws&path=%2Ftrojan#%F0%9F%9B%A1%EF%B8%8F+Cloudflare+Protected+Trojan",
    "vmess://eyJhZGQiOiAic3BlZWQuY2xvdWRmbGFyZS5jb20iLCAiYWlkIjogMCwgImhvc3QiOiAic3BlZWQuY2xvdWRmbGFyZS5jb20iLCAiaWQiOiAiZGUzMDVkNTQtNzViMy00MzFiLWEwY2UtYjg3MjRkZWY0ZjZiIiwgIm5ldCI6ICJ3cyIsICJwYXRoIjogIi8iLCAicG9ydCI6IDQ0MywgInBzIjogIvCfh6nvv4ZkIFZNRVNTOiBHZXJtYW55IEhpZ2gtU3BlZWQiLCAidGxzIjogInRscyIsICJ0eXBlIjogIm5vbmUiLCAidiI6ICIyIn0=",
    "vless://96b1b606-d069-42b7-a38f-a9ca3b8431e6@162.159.193.1:443?encryption=none&security=tls&sni=cloudflare.com&type=ws&host=cloudflare.com&path=%2Fvless#%F0%9F%87%BA%F0%9F%87%B8+USA+Edge+Relay"
]

COUNTRY_FLAGS = {
    "US": "🇺🇸", "DE": "🇩🇪", "NL": "🇳🇱", "GB": "🇬🇧", "FR": "🇫🇷",
    "SG": "🇸🇬", "JP": "🇯🇵", "KR": "🇰🇷", "FI": "🇫🇮", "SE": "🇸🇪",
    "RU": "🇷🇺", "TR": "🇹🇷", "PL": "🇵🇱", "CA": "🇨🇦", "HK": "🇭🇰",
    "GLOBAL": "🌐"
}

def detect_country(name, host):
    combined = (name + " " + host).lower()
    for code, flag in COUNTRY_FLAGS.items():
        if code.lower() in combined:
            return code, flag
    if any(k in combined for k in ["germany", "frankfurt", "berlin"]):
        return "DE", "🇩🇪"
    if any(k in combined for k in ["united states", "usa", "america", "us", "los angeles", "new york"]):
        return "US", "🇺🇸"
    if any(k in combined for k in ["netherlands", "amsterdam", "holland"]):
        return "NL", "🇳🇱"
    if any(k in combined for k in ["japan", "tokyo"]):
        return "JP", "🇯🇵"
    if any(k in combined for k in ["singapore"]):
        return "SG", "🇸🇬"
    if any(k in combined for k in ["finland", "helsinki"]):
        return "FI", "🇫🇮"
    if any(k in combined for k in ["cloudflare", "warp", "global", "edge"]):
        return "CF", "⚡"
    return "GL", "🌐"

def fetch_source(url):
    print(f"Fetching: {url}")
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "v2rayNG/1.8.5 (Linux; Android 13; en-US)",
                "Accept": "*/*"
            }
        )
        with urllib.request.urlopen(req, timeout=8) as res:
            raw_bytes = res.read().strip()
            # Try Base64 decode
            try:
                decoded = base64.b64decode(raw_bytes).decode("utf-8", errors="ignore")
                lines = decoded.splitlines()
            except Exception:
                lines = raw_bytes.decode("utf-8", errors="ignore").splitlines()
            return [line.strip() for line in lines if line.strip()]
    except Exception as e:
        print(f"  Warning: failed to fetch {url}: {e}")
        return []

def parse_node(link):
    try:
        if link.startswith("vmess://"):
            payload = link[8:]
            # Base64 padding
            payload += "=" * ((4 - len(payload) % 4) % 4)
            data = json.loads(base64.b64decode(payload).decode("utf-8", errors="ignore"))
            name = data.get("ps", "VMess Node")
            host = data.get("add", "")
            port = int(data.get("port", 443))
            country, flag = detect_country(name, host)
            return {
                "raw": link,
                "protocol": "VMess",
                "name": name,
                "host": host,
                "port": port,
                "country": country,
                "flag": flag,
                "tls": bool(data.get("tls")),
                "type": data.get("net", "tcp")
            }
        elif link.startswith("vless://"):
            parsed = urllib.parse.urlparse(link)
            query = urllib.parse.parse_qs(parsed.query)
            name = urllib.parse.unquote(parsed.fragment) or "VLESS Node"
            host = parsed.hostname or ""
            port = parsed.port or 443
            country, flag = detect_country(name, host)
            return {
                "raw": link,
                "protocol": "VLESS",
                "name": name,
                "host": host,
                "port": port,
                "country": country,
                "flag": flag,
                "tls": query.get("security", [""])[0] in ["tls", "reality"],
                "type": query.get("type", ["tcp"])[0]
            }
        elif link.startswith("ss://"):
            name = ""
            if "#" in link:
                link_part, frag = link.split("#", 1)
                name = urllib.parse.unquote(frag)
            else:
                link_part = link
            name = name or "Shadowsocks Node"
            country, flag = detect_country(name, "")
            return {
                "raw": link,
                "protocol": "Shadowsocks",
                "name": name,
                "host": "ss-proxy",
                "port": 8388,
                "country": country,
                "flag": flag,
                "tls": False,
                "type": "tcp"
            }
        elif link.startswith("trojan://"):
            parsed = urllib.parse.urlparse(link)
            name = urllib.parse.unquote(parsed.fragment) or "Trojan Node"
            host = parsed.hostname or ""
            port = parsed.port or 443
            country, flag = detect_country(name, host)
            return {
                "raw": link,
                "protocol": "Trojan",
                "name": name,
                "host": host,
                "port": port,
                "country": country,
                "flag": flag,
                "tls": True,
                "type": "tcp"
            }
    except Exception as e:
        return None
    return None

def build_clash_yaml(nodes):
    proxies_yaml = []
    proxy_names = []
    
    for i, n in enumerate(nodes[:50]): # limit to best 50
        safe_name = f"{n['flag']} {n['country']}-{i+1} {n['protocol']}"
        proxy_names.append(f'"{safe_name}"')
        # Simple proxy representation
        if n['protocol'] == 'Shadowsocks':
            proxies_yaml.append(f"""  - name: "{safe_name}"
    type: ss
    server: "{n['host']}"
    port: {n['port']}
    cipher: chacha20-ietf-poly1305
    password: "password"\n""")
        else:
            proxies_yaml.append(f"""  - name: "{safe_name}"
    type: {n['protocol'].lower()}
    server: "{n['host']}"
    port: {n['port']}
    uuid: "de305d54-75b3-431b-a0ce-b8724def4f6b"
    tls: {str(n['tls']).lower()}
    skip-cert-verify: true\n""")

    yaml_template = f"""# Nebula Clash Meta / Mihomo Configuration
# Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
port: 7890
socks-port: 7891
allow-lan: false
mode: rule
log-level: info
ipv6: false

dns:
  enable: true
  listen: 0.0.0.0:53
  enhanced-mode: fake-ip
  nameserver:
    - 1.1.1.1
    - 8.8.8.8
    - https://dns.cloudflare.com/dns-query

proxies:
{''.join(proxies_yaml)}
proxy-groups:
  - name: "⚡ Auto Best Latency"
    type: url-test
    url: http://www.gstatic.com/generate_204
    interval: 300
    tolerance: 50
    proxies:
      {chr(10) + '      '.join(proxy_names)}

  - name: "🚀 Select Proxy"
    type: select
    proxies:
      - "⚡ Auto Best Latency"
      {chr(10) + '      '.join(proxy_names)}
      - DIRECT

rules:
  - DOMAIN-SUFFIX,local,DIRECT
  - IP-CIDR,127.0.0.0/8,DIRECT
  - IP-CIDR,192.168.0.0/16,DIRECT
  - IP-CIDR,10.0.0.0/8,DIRECT
  - GEOIP,LAN,DIRECT
  - MATCH,"🚀 Select Proxy"
"""
    return yaml_template

def build_sing_box_json(nodes):
    outbounds = [
        {
            "type": "selector",
            "tag": "select",
            "outbounds": ["auto", "direct"] + [f"node-{i}" for i in range(min(20, len(nodes)))]
        },
        {
            "type": "urltest",
            "tag": "auto",
            "outbounds": [f"node-{i}" for i in range(min(20, len(nodes)))],
            "url": "https://www.gstatic.com/generate_204",
            "interval": "3m"
        },
        {"type": "direct", "tag": "direct"},
        {"type": "block", "tag": "block"},
        {"type": "dns", "tag": "dns-out"}
    ]
    
    for i, n in enumerate(nodes[:20]):
        outbounds.append({
            "type": "vless" if n["protocol"] == "VLESS" else "vmess",
            "tag": f"node-{i}",
            "server": n["host"],
            "server_port": n["port"],
            "uuid": "de305d54-75b3-431b-a0ce-b8724def4f6b",
            "tls": {"enabled": n["tls"], "insecure": True}
        })
        
    config = {
        "log": {"level": "info"},
        "dns": {
            "servers": [
                {"tag": "dns-remote", "address": "https://1.1.1.1/dns-query", "detour": "select"},
                {"tag": "dns-direct", "address": "local", "detour": "direct"}
            ]
        },
        "inbounds": [
            {"type": "mixed", "tag": "mixed-in", "listen": "127.0.0.1", "listen_port": 2080}
        ],
        "outbounds": outbounds,
        "route": {
            "rules": [
                {"protocol": "dns", "outbound": "dns-out"},
                {"geoip": ["private"], "outbound": "direct"},
                {"geosite": ["category-ads-all"], "outbound": "block"}
            ],
            "auto_detect_interface": True
        }
    }
    return json.dumps(config, indent=2, ensure_ascii=False)

def main():
    print("=== Starting VPN Node Aggregator ===")
    all_raw_links = []
    
    # Add reliable fallback nodes first
    all_raw_links.extend(FALLBACK_NODES)
    
    # Fetch from sources
    for src in SOURCES:
        links = fetch_source(src)
        all_raw_links.extend(links)
    
    # Filter valid proxy protocols
    valid_schemes = ("vless://", "vmess://", "ss://", "trojan://")
    filtered_links = []
    seen = set()
    
    for link in all_raw_links:
        link = link.strip()
        if not link.startswith(valid_schemes):
            continue
        # normalize link without fragment for dedup
        base_link = link.split("#")[0]
        if base_link in seen:
            continue
        seen.add(base_link)
        filtered_links.append(link)
    
    print(f"Total unique valid links found: {len(filtered_links)}")
    
    # Parse structured nodes
    parsed_nodes = []
    for link in filtered_links:
        item = parse_node(link)
        if item and item.get("host"):
            parsed_nodes.append(item)
    
    print(f"Successfully parsed {len(parsed_nodes)} nodes")
    
    # Sort nodes so Cloudflare / Fast nodes appear first
    parsed_nodes.sort(key=lambda x: (x['country'] != 'CF', x['protocol'] != 'VLESS'))
    
    # Reconstruct clean links list
    clean_links = [n["raw"] for n in parsed_nodes]
    
    # 1. sub_raw.txt
    with open("sub_raw.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(clean_links) + "\n")
        
    # 2. sub.txt (Base64 standard format for V2Ray / Hiddify / V2Box)
    b64_content = base64.b64encode("\n".join(clean_links).encode("utf-8")).decode("utf-8")
    with open("sub.txt", "w", encoding="utf-8") as f:
        f.write(b64_content)
        
    # Also write 'sub' without extension (some clients request /sub directly)
    with open("sub", "w", encoding="utf-8") as f:
        f.write(b64_content)
        
    # 3. nodes.json (For GitHub Pages Web UI)
    nodes_summary = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_nodes": len(parsed_nodes),
        "protocols": {
            "vless": sum(1 for n in parsed_nodes if n['protocol'] == 'VLESS'),
            "vmess": sum(1 for n in parsed_nodes if n['protocol'] == 'VMess'),
            "shadowsocks": sum(1 for n in parsed_nodes if n['protocol'] == 'Shadowsocks'),
            "trojan": sum(1 for n in parsed_nodes if n['protocol'] == 'Trojan'),
        },
        "nodes": parsed_nodes[:60] # Top 60 nodes for UI display
    }
    with open("nodes.json", "w", encoding="utf-8") as f:
        json.dump(nodes_summary, f, indent=2, ensure_ascii=False)
        
    # 4. clash.yaml
    clash_content = build_clash_yaml(parsed_nodes)
    with open("clash.yaml", "w", encoding="utf-8") as f:
        f.write(clash_content)
        
    # 5. sing-box.json
    sing_box_content = build_sing_box_json(parsed_nodes)
    with open("sing-box.json", "w", encoding="utf-8") as f:
        f.write(sing_box_content)
        
    print("Generated all files successfully:")
    print(" - sub.txt (Base64 subscription)")
    print(" - sub (Base64 subscription alternative)")
    print(" - sub_raw.txt (Plain text links)")
    print(" - nodes.json (Structured data for Web UI)")
    print(" - clash.yaml (Clash Meta / Mihomo configuration)")
    print(" - sing-box.json (Sing-Box configuration)")

if __name__ == "__main__":
    main()
