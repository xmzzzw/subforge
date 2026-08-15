"""sing-box 配置生成器 —— JSON 格式，与 Surge/Clash 差异最大。

sing-box 特点：
- 用 "outbounds" 表示节点
- 用 "route.rules" 表示规则
- 协议用 type: shadowsocks / trojan / ...
"""
import json
from typing import List
from .base import BaseProducer
from ..models.node import Node


class SingBoxProducer(BaseProducer):
    """生成 sing-box 配置"""

    name = "singbox"

    def generate(self, nodes: List[Node], **kwargs) -> str:
        # sing-box 结构
        config = {
            "log": {"level": "warn", "timestamp": True},
            "inbounds": [{
                "type": "tun",
                "tag": "tun-in",
                "address": ["172.18.0.1/30", "fdfe:dcba:9876::1/126"],
                "auto_route": True,
                "strict_route": False,
                "stack": "system",
            }],
            "outbounds": [{
                "type": "direct",
                "tag": "direct"
            }],
            "route": {
                "rules": [],
                "final": "direct",
                "auto_detect_interface": True,
            },
        }

        # 节点 → outbounds
        node_tags = []
        for n in nodes:
            ob = self._node_outbound(n)
            if ob:
                config["outbounds"].append(ob)
                node_tags.append(n.tagged_name())

        # 规则（简化：AI 走第一个节点，国内直连）
        config["route"]["rules"] = [
            {
                "rule_set": [],
                "outbound": "direct",
            }
        ]
        if node_tags:
            config["route"]["final"] = node_tags[0]

        return json.dumps(config, ensure_ascii=False, indent=2)

    def _node_outbound(self, node: Node) -> dict | None:
        params = node.params
        name = node.tagged_name()

        if node.protocol == "ss":
            return {
                "type": "shadowsocks", "tag": name,
                "server": node.server, "server_port": node.port,
                "method": params.get("cipher", "aes-256-gcm"),
                "password": params.get("password", ""),
            }
        elif node.protocol == "trojan":
            ob = {
                "type": "trojan", "tag": name,
                "server": node.server, "server_port": node.port,
                "password": params.get("password", ""),
                "tls": {"enabled": True, "insecure": True},
            }
            if "sni" in params:
                ob["tls"]["server_name"] = params["sni"]
            return ob
        elif node.protocol == "anytls":
            return {
                "type": "anytls", "tag": name,
                "server": node.server, "server_port": node.port,
                "password": params.get("password", ""),
                "tls": {"enabled": True, "insecure": True},
            }
        elif node.protocol == "vmess":
            return {
                "type": "vmess", "tag": name,
                "server": node.server, "server_port": node.port,
                "uuid": params.get("uuid", ""),
                "security": params.get("cipher", "auto"),
            }
        return None
