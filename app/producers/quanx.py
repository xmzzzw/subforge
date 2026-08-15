"""Quantumult X 配置生成器 —— 格式与 Surge/Loon 差异较大。

QX 特点：
- 节点用 [server_local] 段
- 策略组用 [policy] 段（static/url-latency-benchmark）
- 规则用 [filter_local] 段（引用远程 filter_remote）
"""
from typing import List
from .base import BaseProducer
from ..models.node import Node
from ..transforms.group import CountryGroupBuilder

# QX 规则集引用
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


class QuanXProducer(BaseProducer):
    """生成 Quantumult X 配置"""

    name = "quanx"

    def generate(self, nodes: List[Node], **kwargs) -> str:
        builder = CountryGroupBuilder()
        groups, by_country = builder.build_groups(nodes, kwargs.get("transforms"))

        out = []
        # server_local（节点）
        out.append("[server_local]")
        for n in nodes:
            line = self._node_line(n)
            if line:
                out.append(line)
        out.append("")

        # policy（策略组）
        out.append("[policy]")
        for g in groups:
            members = ", ".join(g["members"])
            if g["type"] == "select":
                out.append(f"static={g['name']}, {members}")
            elif g["type"] == "url-test":
                # QX 用 url-latency-benchmark + server-tag-regex
                regex = "|".join(g["members"])
                out.append(f"url-latency-benchmark={g['name']}, server-tag-regex='({regex})'")
        out.append("")

        # filter_local（规则）
        out.append("[filter_local]")
        for file, policy in RULESET_MAP:
            out.append(f"host-suffix, {file.rstrip('.list')}, {policy}")
        out.append("geoip, cn, 🎯Direct")
        out.append("final, ✈️Final")
        out.append("")
        return "\n".join(out)

    def _node_line(self, node: Node) -> str:
        params = node.params
        name = node.tagged_name()

        if node.protocol == "ss":
            # QX ss 格式: shadowsocks=host:port, method=cipher, password=pass, fast-open=false, udp-relay=true, tag=name
            return (f"shadowsocks={node.server}:{node.port}, "
                    f"method={params.get('cipher', 'aes-256-gcm')}, "
                    f"password={params.get('password', '')}, "
                    f"udp-relay=true, tag={name}")
        elif node.protocol == "trojan":
            return (f"trojan={node.server}:{node.port}, "
                    f"password={params.get('password', '')}, "
                    f"over-tls=true, tls-verification=false, "
                    f"tag={name}")
        elif node.protocol == "anytls":
            return (f"anytls={node.server}:{node.port}, "
                    f"password={params.get('password', '')}, "
                    f"over-tls=true, tls-verification=false, "
                    f"tag={name}")
        elif node.protocol == "vmess":
            return (f"vmess={node.server}:{node.port}, "
                    f"username={params.get('uuid', '')}, "
                    f"tag={name}")
        else:
            return None  # 不支持的协议跳过
