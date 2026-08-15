"""协议识别 —— 从文本自动识别节点协议。"""
import re
from typing import Optional

# 支持的协议
PROTOCOLS = [
    "ss", "ssr", "trojan", "anytls", "vmess", "vless",
    "hysteria", "hysteria2", "tuic", "wireguard", "snell",
    "http", "socks5", "socks",
]

# Surge 行格式: name = ss, server, port, params
SURGE_PATTERN = re.compile(r'^(.+?)\s*=\s*(\w+)\s*,\s*(.+)$')

# URI 格式: ss://base64@host:port#name
URI_PATTERNS = {
    "ss": re.compile(r'^ss://'),
    "ssr": re.compile(r'^ssr://'),
    "trojan": re.compile(r'^trojan://'),
    "anytls": re.compile(r'^anytls://'),
    "vmess": re.compile(r'^vmess://'),
    "vless": re.compile(r'^vless://'),
    "hysteria": re.compile(r'^hysteria://'),
    "hysteria2": re.compile(r'^hysteria2://'),
    "tuic": re.compile(r'^tuic://'),
    "wireguard": re.compile(r'^wireguard://'),
    "snell": re.compile(r'^snell://'),
}


def detect_protocol(text: str) -> Optional[str]:
    """识别文本片段使用的协议"""
    text = text.strip()
    # 1. URI 形式
    for proto, pattern in URI_PATTERNS.items():
        if pattern.match(text):
            return proto
    # 2. Surge 行形式
    m = SURGE_PATTERN.match(text)
    if m:
        proto = m.group(2).lower()
        if proto in PROTOCOLS:
            return proto
    # 3. Clash YAML type 字段
    m = re.search(r'type:\s*["\']?(\w+)', text)
    if m and m.group(1).lower() in PROTOCOLS:
        return m.group(1).lower()
    return None


def detect_all_protocols(lines: list[str]) -> dict[str, int]:
    """统计一批行中的协议分布"""
    from collections import Counter
    counter = Counter()
    for line in lines:
        p = detect_protocol(line)
        if p:
            counter[p] += 1
    return dict(counter)
