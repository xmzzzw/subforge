"""Surge 配置生成器 —— 生成 .conf 格式配置。"""
from typing import List
from .base import BaseProducer
from ..models.node import Node
from ..transforms.group import CountryGroupBuilder

# 规则集引用（my-rulesets）
RULE_BASE = "https://raw.githubusercontent.com/xmzzzw/my-rulesets/main"
RULESET_MAP = [
    ("nexitallyy_Extra_CN_3.list", "🎯Direct"), ("blackmatrix7_GlobalScholar.list", "Scholar"),
    ("blackmatrix7_myTVSUPER.list", "MyTVSuper"), ("nexitallyy_Extra_Crypto.list", "Crypto"),
    ("nexitallyy_Extra_AI.list", "AI"), ("blackmatrix7_Google.list", "Google"),
    ("ACL4SSR_YouTube.list", "YouTube"), ("blackmatrix7_GameDownload.list", "🎯Direct"),
    ("ACL4SSR_LocalAreaNetwork.list", "🎯Direct"), ("ACL4SSR_ChinaCompanyIp.list", "🎯Direct"),
    ("HotKids_Netflix.list", "Netflix"), ("ACL4SSR_Telegram.list", "Telegram"),
    ("blackmatrix7_Steam.list", "Steam"), ("blackmatrix7_Epic.list", "Epic"),
    ("blackmatrix7_Xbox.list", "Xbox"), ("blackmatrix7_PlayStation.list", "PlayStation"),
    ("HotKids_HBO_Max.list", "HBO"), ("blackmatrix7_HBOUSA.list", "HBO"),
    ("blackmatrix7_HBOHK.list", "HBO"), ("naiixi_DisneyPlus.list", "DisneyPlus"),
    ("ACL4SSR_Bahamut.list", "Bahamut"), ("HotKids_Bilibili.list", "Bilibili"),
    ("ACL4SSR_Microsoft.list", "Microsoft"), ("ACL4SSR_Apple.list", "Apple"),
    ("blackmatrix7_TikTok.list", "Tiktok"), ("ACL4SSR_ProxyLite.list", "Proxies"),
    ("blackmatrix7_Facebook.list", "Proxies"), ("nexitallyy_Extra_Proxies.list", "Proxies"),
    ("blackmatrix7_Twitter.list", "Proxies"), ("naiixi_Extra_CN.list", "🎯Direct"),
    ("naiixi_Extra_CN_2.list", "🎯Direct"), ("blackmatrix7_WeChat.list", "🎯Direct"),
]


class SurgeProducer(BaseProducer):
    """生成 Surge 配置"""

    name = "surge"

    def generate(self, nodes: List[Node], **kwargs) -> str:
        # 构建策略组
        builder = CountryGroupBuilder()
        groups, by_country = builder.build_groups(nodes, kwargs.get("transforms"))

        out = []
        # General
        out.append("[General]")
        out.append("loglevel = notify")
        out.append("dns-server = 119.29.29.29, 223.5.5.5")
        out.append("bypass-system = true")
        out.append("proxy-test-url = http://www.gstatic.com/generate_204")
        out.append("encrypted-dns-server = https://dns.alidns.com/dns-query, https://doh.pub/dns-query")
        out.append("")

        # Proxy 段
        out.append("[Proxy]")
        out.append("DIRECT = direct")
        for n in nodes:
            out.append(self._node_line(n))
        out.append("")

        # Proxy Group 段
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

        # Rule 段
        out.append("[Rule]")
        for file, policy in RULESET_MAP:
            out.append(f"RULE-SET,{RULE_BASE}/{file},{policy},update-interval=86400")
        out.append("GEOIP,CN,🎯Direct")
        out.append("FINAL,✈️Final")
        out.append("")

        return "\n".join(out)

    def _node_line(self, node: Node) -> str:
        """生成 Surge 节点行"""
        params = node.params
        name = node.tagged_name()

        if node.protocol == "ss":
            line = (f"{name} = ss, {node.server}, {node.port}, "
                    f"encrypt-method={params.get('cipher', 'aes-256-gcm')}, "
                    f"password={params.get('password', '')}, "
                    f"udp-relay=true")
            if params.get("obfs") == "http" or params.get("plugin") == "obfs":
                host = params.get("obfs-host", "") or params.get("host", "")
                line += f", obfs=http, obfs-host={host}"
            return line
        elif node.protocol == "trojan":
            line = (f"{name} = trojan, {node.server}, {node.port}, "
                    f"password={params.get('password', '')}")
            if "sni" in params:
                line += f", sni={params['sni']}"
            elif params.get("host"):
                line += f", sni={params['host']}"
            line += ", skip-cert-verify=true, udp-relay=true"
            return line
        elif node.protocol == "anytls":
            line = (f"{name} = anytls, {node.server}, {node.port}, "
                    f"password={params.get('password', '')}")
            if "sni" in params:
                line += f", sni={params['sni']}"
            line += ", skip-cert-verify=true, udp-relay=true"
            return line
        elif node.protocol == "vmess":
            line = (f"{name} = vmess, {node.server}, {node.port}, "
                    f"username={params.get('uuid', '')}, "
                    f"encrypt-method={params.get('cipher', 'auto')}")
            return line
        else:
            # 通用格式（尽力而为）
            extra = ", ".join(f"{k}={v}" for k, v in params.items())
            return f"{name} = {node.protocol}, {node.server}, {node.port}, {extra}"
