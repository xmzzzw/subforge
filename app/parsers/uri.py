"""URI 协议解析器 —— 解析 ss:// trojan:// anytls:// 等协议链接。"""
import base64
import re
from typing import List
from urllib.parse import urlparse, unquote
from .base import BaseParser
from ..models.node import Node


class URIParser(BaseParser):
    """解析协议 URI（ss://trojan://anytls://vmess://...）"""

    name = "uri"

    def parse(self, content: str) -> List[Node]:
        nodes = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            node = self._parse_uri(line)
            if node:
                nodes.append(node)
        return nodes

    def _parse_uri(self, uri: str) -> Node | None:
        try:
            if uri.startswith("ss://"):
                return self._parse_ss(uri)
            elif uri.startswith("ssr://"):
                return self._parse_ssr(uri)
            elif uri.startswith("trojan://"):
                return self._parse_trojan(uri, "trojan")
            elif uri.startswith("anytls://"):
                return self._parse_trojan(uri, "anytls")
            elif uri.startswith("vless://"):
                return self._parse_vless(uri)
            elif uri.startswith("vmess://"):
                return self._parse_vmess(uri)
            elif uri.startswith("hysteria2://") or uri.startswith("hysteria://"):
                return self._parse_hysteria(uri)
            elif uri.startswith("tuic://"):
                return self._parse_tuic(uri)
        except Exception:
            return None
        return None

    def _extract_name(self, uri: str) -> str:
        """提取 URI 里的 #name"""
        if "#" in uri:
            return unquote(uri.split("#", 1)[1])
        return ""

    def _parse_ss(self, uri: str) -> Node | None:
        name = self._extract_name(uri)
        body = uri.split("#", 1)[0][len("ss://"):]
        # 支持 userinfo@host:port 或 base64 形式
        if "@" in body:
            auth, _, hostpart = body.rpartition("@")
            # auth 可能是 base64 (method:password) 或明文
            if ":" not in auth:
                try:
                    auth = base64.b64decode(auth).decode()
                except Exception:
                    pass
            if ":" in auth:
                method, _, password = auth.partition(":")
            else:
                method, password = "aes-256-gcm", auth
            host, _, port = hostpart.partition(":")
            port = int(port)
        else:
            # base64 形式 ss://base64(method:password@host:port)
            try:
                decoded = base64.b64decode(body).decode()
                auth, _, hostpart = decoded.rpartition("@")
                method, _, password = auth.partition(":")
                host, _, port = hostpart.partition(":")
                port = int(port)
            except Exception:
                return None
        return Node(name=name or host, protocol="ss", server=host, port=port,
                    params={"cipher": method, "password": password})

    def _parse_ssr(self, uri: str) -> Node | None:
        # ssr://base64
        name = self._extract_name(uri)
        try:
            body = uri.split("#", 1)[0][len("ssr://"):]
            decoded = base64.b64decode(body + "==").decode()
            # server:port:protocol:method:obfs:password_base64/?params#name
            parts = decoded.split(":", 5)
            if len(parts) < 6:
                return None
            server, port, proto, method, obfs, rest = parts
            password_b64 = rest.split("/", 1)[0]
            password = base64.b64decode(password_b64 + "==").decode()
            return Node(name=name or server, protocol="ssr", server=server,
                        port=int(port),
                        params={"cipher": method, "password": password,
                                "protocol": proto, "obfs": obfs})
        except Exception:
            return None

    def _parse_trojan(self, uri: str, proto: str) -> Node | None:
        name = self._extract_name(uri)
        parsed = urlparse(uri)
        password = parsed.username or ""
        server = parsed.hostname or ""
        port = parsed.port or 443
        params = {"password": password}
        # 查询参数
        if parsed.query:
            for kv in parsed.query.split("&"):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    params[k] = v
        if "sni" not in params:
            params["sni"] = server
        return Node(name=name or server, protocol=proto, server=server,
                    port=port, params=params)

    def _parse_vless(self, uri: str) -> Node | None:
        name = self._extract_name(uri)
        parsed = urlparse(uri)
        uuid = parsed.username or ""
        server = parsed.hostname or ""
        port = parsed.port or 443
        params = {"uuid": uuid}
        if parsed.query:
            for kv in parsed.query.split("&"):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    params[k] = v
        return Node(name=name or server, protocol="vless", server=server,
                    port=port, params=params)

    def _parse_vmess(self, uri: str) -> Node | None:
        # vmess://base64(JSON)
        name = self._extract_name(uri)
        try:
            body = uri.split("#", 1)[0][len("vmess://"):]
            decoded = base64.b64decode(body).decode()
            import json
            data = json.loads(decoded)
            return Node(name=name or data.get("ps", data.get("add", "")),
                        protocol="vmess", server=data.get("add", ""),
                        port=int(data.get("port", 0)),
                        params={"uuid": data.get("id", ""),
                                "cipher": data.get("type", "auto"),
                                "alterId": data.get("aid", 0)})
        except Exception:
            return None

    def _parse_hysteria(self, uri: str) -> Node | None:
        name = self._extract_name(uri)
        parsed = urlparse(uri)
        server = parsed.hostname or ""
        port = parsed.port or 443
        params = {}
        if parsed.query:
            for kv in parsed.query.split("&"):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    params[k] = v
        proto = "hysteria2" if uri.startswith("hysteria2://") else "hysteria"
        return Node(name=name or server, protocol=proto, server=server,
                    port=port, params=params)

    def _parse_tuic(self, uri: str) -> Node | None:
        name = self._extract_name(uri)
        parsed = urlparse(uri)
        server = parsed.hostname or ""
        port = parsed.port or 443
        params = {"password": parsed.username or "", "uuid": parsed.password or ""}
        return Node(name=name or server, protocol="tuic", server=server,
                    port=port, params=params)
