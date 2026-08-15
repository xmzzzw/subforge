"""Clash/mihomo 配置生成器 —— 生成 YAML 格式。"""
from typing import List
import yaml
from .base import BaseProducer
from ..models.node import Node
from ..transforms.group import CountryGroupBuilder

# 规则集引用（clash/ 目录）
RULE_BASE = "https://raw.githubusercontent.com/xmzzzw/my-rulesets/main/clash"
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


class ClashProducer(BaseProducer):
    """生成 Clash/mihomo 配置"""

    name = "clash"

    def generate(self, nodes: List[Node], **kwargs) -> str:
        builder = CountryGroupBuilder()
        groups, by_country = builder.build_groups(nodes, kwargs.get("transforms"))

        config = {
            "mixed-port": 7890, "allow-lan": False, "mode": "rule",
            "log-level": "warning", "ipv6": True,
            "dns": {
                "enable": True, "enhanced-mode": "fake-ip",
                "fake-ip-range": "198.18.0.1/16",
                "fake-ip-filter": ["*.lan", "+.local", "+.msftconnecttest.com", "+.msftncsi.com"],
                "default-nameserver": ["223.5.5.5", "119.29.29.29"],
                "nameserver": ["https://223.5.5.5/dns-query", "https://doh.pub/dns-query"],
                "fallback": ["https://1.1.1.1/dns-query", "https://dns.google/dns-query"],
                "fallback-filter": {"geoip": True, "geoip-code": "CN"},
            },
            "proxies": [self._node_dict(n) for n in nodes],
            "proxy-groups": [],
            "rule-providers": {},
            "rules": [],
        }

        # proxy-groups
        for g in groups:
            group = {"name": g["name"], "type": g["type"], "proxies": g["members"]}
            if g["type"] == "url-test":
                group["url"] = g.get("url", "http://www.gstatic.com/generate_204")
                group["interval"] = int(g.get("interval", 300))
                if "tolerance" in g:
                    group["tolerance"] = int(g["tolerance"])
            config["proxy-groups"].append(group)

        # rule-providers
        for i, (file, policy) in enumerate(RULESET_MAP):
            pid = f"provider_{i}"
            config["rule-providers"][pid] = {
                "type": "http", "behavior": "classical", "format": "text",
                "url": f"{RULE_BASE}/{file}", "path": f"./providers/{file}",
                "interval": 86400,
            }
            config["rules"].append(f"RULE-SET,{pid},{policy}")

        config["rules"].append("GEOIP,CN,🎯Direct,no-resolve")
        config["rules"].append("MATCH,✈️Final")

        return yaml.dump(config, allow_unicode=True, sort_keys=False, default_flow_style=False)

    def _node_dict(self, node: Node) -> dict:
        """生成 Clash 节点字典"""
        params = node.params
        name = node.tagged_name()
        proxy = {"name": name, "type": node.protocol, "server": node.server, "port": node.port}

        if node.protocol == "ss":
            proxy["cipher"] = params.get("cipher", "aes-256-gcm")
            proxy["password"] = params.get("password", "")
            proxy["udp"] = True
            if params.get("obfs") == "http" or params.get("plugin") == "obfs":
                proxy["plugin"] = "obfs"
                proxy["plugin-opts"] = {"mode": "http", "host": params.get("obfs-host", "")}
        elif node.protocol in ("trojan", "anytls"):
            proxy["password"] = params.get("password", "")
            if "sni" in params:
                proxy["sni"] = params["sni"]
            elif params.get("host"):
                proxy["sni"] = params["host"]
            proxy["skip-cert-verify"] = params.get("skip-cert-verify", "false").lower() in ("true", "1")
            proxy["udp"] = True
        elif node.protocol in ("vmess", "vless"):
            proxy["uuid"] = params.get("uuid", "")
            proxy["alterId"] = int(params.get("alterId", 0) or 0)
            proxy["cipher"] = params.get("cipher", "auto")
            proxy["udp"] = True
            if "network" in params:
                proxy["network"] = params["network"]
            # TLS
            if "tls" in params:
                proxy["tls"] = params["tls"]
            if "servername" in params:
                proxy["servername"] = params["servername"]
            # WebSocket 传输
            if "ws-opts" in params and isinstance(params["ws-opts"], dict):
                proxy["ws-opts"] = params["ws-opts"]
            elif "ws-path" in params:
                proxy["ws-opts"] = {"path": params["ws-path"]}
                if "host" in params:
                    proxy["ws-opts"]["headers"] = {"Host": params["host"]}
            elif params.get("network") == "ws":
                ws_opts = {}
                if params.get("ws-path"):
                    ws_opts["path"] = params["ws-path"]
                if params.get("host"):
                    ws_opts["headers"] = {"Host": params["host"]}
                if ws_opts:
                    proxy["ws-opts"] = ws_opts
            # gRPC
            if "grpc-opts" in params and isinstance(params["grpc-opts"], dict):
                proxy["grpc-opts"] = params["grpc-opts"]
            elif params.get("grpc-service-name"):
                proxy["grpc-opts"] = {"grpc-service-name": params["grpc-service-name"]}
            # 底层传输
            for k in ("reality-opts", "client-fingerprint", "flow"):
                if k in params:
                    proxy[k] = params[k]
        elif node.protocol in ("hysteria", "hysteria2"):
            proxy["password"] = params.get("password", "")
            if "sni" in params:
                proxy["sni"] = params["sni"]
            proxy["skip-cert-verify"] = params.get("skip-cert-verify", False)
            if "obfs" in params:
                proxy["obfs"] = params["obfs"]
            if "obfs-password" in params:
                proxy["obfs-password"] = params["obfs-password"]
            if "up" in params:
                proxy["up"] = params["up"]
            if "down" in params:
                proxy["down"] = params["down"]
        else:
            # 通用：透传
            proxy.update(params)

        return proxy
