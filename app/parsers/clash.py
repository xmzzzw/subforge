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
            # TLS
            if "tls" in p:
                params["tls"] = p["tls"]
            if "servername" in p:
                params["servername"] = p["servername"]
            # WebSocket 传输
            ws_opts = p.get("ws-opts") or {}
            if ws_opts:
                params["ws-opts"] = ws_opts
                if "path" in ws_opts:
                    params["ws-path"] = ws_opts["path"]
                if "headers" in ws_opts and ws_opts["headers"].get("Host"):
                    params["host"] = ws_opts["headers"]["Host"]
            # gRPC
            grpc_opts = p.get("grpc-opts") or {}
            if grpc_opts:
                params["grpc-opts"] = grpc_opts
                if "grpc-service-name" in grpc_opts:
                    params["grpc-service-name"] = grpc_opts["grpc-service-name"]
            # 底层传输
            for k in ("reality-opts", "client-fingerprint", "flow"):
                if p.get(k):
                    params[k] = p[k]
        elif proto in ("hysteria", "hysteria2"):
            params["password"] = p.get("password", "")
            if "sni" in p:
                params["sni"] = p["sni"]
            params["skip-cert-verify"] = p.get("skip-cert-verify", False)
            if "obfs" in p:
                params["obfs"] = p["obfs"]
            if "obfs-password" in p:
                params["obfs-password"] = p["obfs-password"]
            if "up" in p:
                params["up"] = p["up"]
            if "down" in p:
                params["down"] = p["down"]
        elif proto == "tuic":
            params["password"] = p.get("password", "")
            params["uuid"] = p.get("uuid", "")
        else:
            # 通用：透传所有字段
            params.update({k: v for k, v in p.items()
                           if k not in ("name", "type", "server", "port")})

        return Node(name=name, protocol=proto, server=server, port=port, params=params)
