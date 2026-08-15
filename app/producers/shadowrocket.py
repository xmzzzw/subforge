"""Shadowrocket 配置生成器 —— 格式接近 Surge。"""
from typing import List
from .base import BaseProducer
from ..models.node import Node
from ..transforms.group import CountryGroupBuilder
from .surge import RULE_BASE, RULESET_MAP


class ShadowrocketProducer(BaseProducer):
    """生成 Shadowrocket 配置（iOS 客户端）"""

    name = "shadowrocket"

    def generate(self, nodes: List[Node], **kwargs) -> str:
        builder = CountryGroupBuilder()
        groups, by_country = builder.build_groups(nodes, kwargs.get("transforms"))

        out = []
        out.append("[General]")
        out.append("loglevel = notify")
        out.append("dns-server = 119.29.29.29, 223.5.5.5")
        out.append("")
        out.append("[Proxy]")
        for n in nodes:
            out.append(self._node_line(n))
        out.append("")
        out.append("[Proxy Group]")
        for g in groups:
            if g["type"] == "select":
                out.append(f"{g['name']} = select, " + ", ".join(g["members"]))
            elif g["type"] == "url-test":
                out.append(
                    f"{g['name']} = url-test, " + ", ".join(g["members"]) +
                    f", url={g['url']}, interval={g['interval']}, tolerance={g['tolerance']}"
                )
        out.append("")
        out.append("[Rule]")
        for file, policy in RULESET_MAP:
            out.append(f"RULE-SET,{RULE_BASE}/{file},{policy},update-interval=86400")
        out.append("GEOIP,CN,🎯Direct")
        out.append("FINAL,✈️Final")
        out.append("")
        return "\n".join(out)

    def _node_line(self, node: Node) -> str:
        params = node.params
        name = node.tagged_name()

        if node.protocol == "ss":
            line = (f"{name} = ss, {node.server}, {node.port}, "
                    f"encrypt-method={params.get('cipher', 'aes-256-gcm')}, "
                    f"password={params.get('password', '')}, udp-relay=true")
            if params.get("obfs") == "http":
                line += f", obfs=http, obfs-host={params.get('obfs-host', '')}"
            return line
        elif node.protocol == "trojan":
            line = (f"{name} = trojan, {node.server}, {node.port}, "
                    f"password={params.get('password', '')}")
            if "sni" in params:
                line += f", sni={params['sni']}"
            line += ", skip-cert-verify=true, udp-relay=true"
            return line
        elif node.protocol == "anytls":
            line = (f"{name} = anytls, {node.server}, {node.port}, "
                    f"password={params.get('password', '')}")
            if "sni" in params:
                line += f", sni={params['sni']}"
            line += ", skip-cert-verify=true, udp-relay=true"
            return line
        else:
            extra = ", ".join(f"{k}={v}" for k, v in params.items())
            return f"{name} = {node.protocol}, {node.server}, {node.port}, {extra}"
