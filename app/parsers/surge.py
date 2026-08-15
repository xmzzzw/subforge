"""Surge 配置解析器 —— 解析 .conf 文件的 [Proxy] 段。"""
import re
from typing import List
from .base import BaseParser
from ..models.node import Node


class SurgeParser(BaseParser):
    """解析 Surge .conf 格式

    支持格式: name = proto, server, port, param=value, ...
    """

    name = "surge"

    # 支持在 Surge 行里出现的协议
    PROTOCOLS = {"ss", "ssr", "trojan", "anytls", "vmess", "vless",
                 "hysteria", "hysteria2", "tuic", "wireguard", "snell",
                 "http", "socks5", "socks"}

    # 伪节点（Traffic/Expire/流量/到期/Panel 等显示用）
    PSEUDO_PATTERNS = [
        r'^Traffic', r'^Expire', r'^流量', r'^到期', r'^已用',
        r'^Panel', r'^面板', r'^剩余', r'^总流量',
    ]

    def parse(self, content: str) -> List[Node]:
        nodes = []
        in_proxy = False
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("[Proxy]"):
                in_proxy = True
                continue
            if in_proxy and line.startswith("["):
                break
            if not in_proxy or not line or line.startswith("#") or line.startswith("//"):
                continue
            # Direct 等直连项跳过
            if " = direct" in line.lower():
                continue
            node = self._parse_line(line)
            if node:
                nodes.append(node)
        return nodes

    def _parse_line(self, line: str) -> Node | None:
        m = re.match(r'^(.+?)\s*=\s*(\w+)\s*,\s*(.+)$', line)
        if not m:
            return None
        name, proto, rest = m.groups()
        name = name.strip()
        proto = proto.lower()

        # 跳过伪节点
        for pat in self.PSEUDO_PATTERNS:
            if re.match(pat, name):
                return None
        # 跳过 "Direct" 显示项
        if name.upper() == "DIRECT" or name.startswith(("当前", "到期")):
            return None

        if proto not in self.PROTOCOLS:
            return None

        parts = [p.strip() for p in rest.split(",")]
        if len(parts) < 2:
            return None
        server = parts[0]
        try:
            port = int(parts[1])
        except (ValueError, IndexError):
            return None

        # 解析参数
        params = {}
        for p in parts[2:]:
            if "=" in p:
                k, v = p.split("=", 1)
                params[k.strip()] = v.strip()

        return Node(
            name=name,
            protocol=proto,
            server=server,
            port=port,
            params=params,
        )
