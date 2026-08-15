"""Clash YAML 解析器 —— 解析 proxies 段。"""
import yaml
from typing import List
from .base import BaseParser
from ..models.node import Node


class ClashParser(BaseParser):
    """解析 Clash YAML 的 proxies 段"""

    name = "clash"

    def parse(self, content: str) -> List[Node]:
        try:
            data = yaml.safe_load(content)
        except Exception:
            return []
        if not data or "proxies" not in data:
            return []

        nodes = []
        for p in data["proxies"]:
            node = self._parse_proxy(p)
            if node:
                nodes.append(node)
        return nodes

    def _parse_proxy(self, p: dict) -> Node | None:
        name = str(p.get("name", ""))
        proto = str(p.get("type", "")).lower()
        server = str(p.get("server", ""))
        port = int(p.get("port", 0))

        # 跳过伪节点
        if name.startswith(("Traffic", "Expire", "流量", "到期", "Panel", "已用", "剩余")):
            return None

        params = {}
        if proto == "ss":
            params["cipher"] = p.get("cipher", "aes-256-gcm")
            params["password"] = p.get("password", "")
            if "plugin" in p:
                params["plugin"] = p["plugin"]
                params["plugin-opts"] = p.get("plugin-opts", {})
        elif proto in ("trojan", "anytls"):
            params["password"] = p.get("password", "")
            if "sni" in p:
                params["sni"] = p["sni"]
            params["skip-cert-verify"] = p.get("skip-cert-verify", False)
        elif proto in ("vmess", "vless"):
            params["uuid"] = p.get("uuid", "")
            params["alterId"] = p.get("alterId", 0)
            params["cipher"] = p.get("cipher", "auto")
            if "network" in p:
                params["network"] = p["network"]
        elif proto in ("hysteria", "hysteria2"):
            params["password"] = p.get("password", "")
            if "sni" in p:
                params["sni"] = p["sni"]
            params["skip-cert-verify"] = p.get("skip-cert-verify", False)
        elif proto == "tuic":
            params["password"] = p.get("password", "")
            params["uuid"] = p.get("uuid", "")
        else:
            # 通用：透传所有字段
            params.update({k: v for k, v in p.items()
                           if k not in ("name", "type", "server", "port")})

        return Node(name=name, protocol=proto, server=server, port=port, params=params)
