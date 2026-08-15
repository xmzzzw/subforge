"""Loon 配置生成器 —— Loon 是 iOS 客户端，格式类似 Surge。"""
from typing import List
from .base import BaseProducer
from ..models.node import Node
from ..transforms.group import CountryGroupBuilder

# Loon 规则集引用
RULE_BASE = "https://raw.githubusercontent.com/xmzzzw/my-rulesets/main"
RULESET_MAP = [
    ("nexitallyy_Extra_CN_3.list", "🎯Direct"), ("blackmatrix7_GlobalScholar.list", "Scholar"),
    ("blackmatrix7_myTVSUPER.list", "MyTVSuper"), ("nexitallyy_Extra_Crypto.list", "Crypto"),
    ("nexitallyy_Extra_AI.list", "AI"), ("blackmatrix7_Google.list", "Google"),
    ("ACL4SSR_YouTube.list", "YouTube"), ("HotKids_Netflix.list", "Netflix"),
    ("ACL4SSR_Telegram.list", "Telegram"), ("blackmatrix7_Steam.list", "Steam"),
    ("blackmatrix7_Epic.list", "Epic"), ("blackmatrix7_Xbox.list", "Xbox"),
    ("blackmatrix7_PlayStation.list", "PlayStation"), ("HotKids_HBO_Max.list", "HBO"),
    ("blackmatrix7_HBOUSA.list", "HBO"), ("blackmatrix7_HBOHK.list", "HBO"),
    ("naiixi_DisneyPlus.list", "DisneyPlus"), ("ACL4SSR_Bahamut.list", "Bahamut"),
    ("HotKids_Bilibili.list", "Bilibili"), ("ACL4SSR_Microsoft.list", "Microsoft"),
    ("ACL4SSR_Apple.list", "Apple"), ("blackmatrix7_TikTok.list", "Tiktok"),
    ("blackmatrix7_Twitter.list", "Proxies"), ("blackmatrix7_Facebook.list", "Proxies"),
    ("nexitallyy_Extra_Proxies.list", "Proxies"), ("naiixi_Extra_CN.list", "🎯Direct"),
    ("naiixi_Extra_CN_2.list", "🎯Direct"), ("blackmatrix7_WeChat.list", "🎯Direct"),
]


class LoonProducer(BaseProducer):
    """生成 Loon 配置（格式接近 Surge）"""

    name = "loon"

    def generate(self, nodes: List[Node], **kwargs) -> str:
        builder = CountryGroupBuilder()
        groups, by_country = builder.build_groups(nodes, kwargs.get("transforms"))

        out = []
        # General
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
                    f"password={params.get('password', '')}, udp=true")
            if params.get("obfs") == "http":
                line += f", obfs=http, obfs-host={params.get('obfs-host', '')}"
            return line
        elif node.protocol == "trojan":
            line = (f"{name} = trojan, {node.server}, {node.port}, "
                    f"password={params.get('password', '')}")
            if "sni" in params:
                line += f", sni={params['sni']}"
            line += ", skip-cert-verify=true, udp=true"
            return line
        elif node.protocol == "anytls":
            line = (f"{name} = anytls, {node.server}, {node.port}, "
                    f"password={params.get('password', '')}")
            if "sni" in params:
                line += f", sni={params['sni']}"
            line += ", skip-cert-verify=true, udp=true"
            return line
        else:
            extra = ", ".join(f"{k}={v}" for k, v in params.items())
            return f"{name} = {node.protocol}, {node.server}, {node.port}, {extra}"
