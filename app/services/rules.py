"""规则集管理 —— 内置 my-rulesets + 自定义规则集。

规则集来源：
1. my-rulesets GitHub 仓库（默认内置）
2. 自定义 URL / 本地文件
"""
import json
import os
import uuid
from typing import List, Optional

# my-rulesets 内置规则集（Surge 格式）
MYRULESETS_SURGE_BASE = "https://raw.githubusercontent.com/xmzzzw/my-rulesets/main"
# my-rulesets 内置规则集（Clash 格式）
MYRULESETS_CLASH_BASE = "https://raw.githubusercontent.com/xmzzzw/my-rulesets/main/clash"

# 内置规则集清单（文件名, 用途）
BUILTIN_RULESETS = [
    ("nexitallyy_Extra_AI.list", "AI 平台（OpenAI/Claude/Gemini/opencode）"),
    ("nexitallyy_Extra_CN_3.list", "强制直连（含国内模型 API）"),
    ("nexitallyy_Extra_Crypto.list", "加密货币"),
    ("nexitallyy_Extra_Proxies.list", "代理名单"),
    ("blackmatrix7_Google.list", "Google"),
    ("blackmatrix7_YouTube.list", "YouTube"),
    ("blackmatrix7_Netflix.list", "Netflix"),
    ("blackmatrix7_Telegram.list", "Telegram"),
    ("blackmatrix7_Steam.list", "Steam"),
    ("blackmatrix7_Epic.list", "Epic"),
    ("blackmatrix7_Xbox.list", "Xbox"),
    ("blackmatrix7_PlayStation.list", "PlayStation"),
    ("blackmatrix7_Microsoft.list", "Microsoft"),
    ("blackmatrix7_Apple.list", "Apple"),
    ("blackmatrix7_TikTok.list", "TikTok"),
    ("blackmatrix7_Twitter.list", "Twitter"),
    ("blackmatrix7_Facebook.list", "Facebook"),
    ("blackmatrix7_WeChat.list", "微信"),
    ("naiixi_Extra_CN.list", "国内直连"),
    ("naiixi_Extra_CN_2.list", "国内直连（China）"),
    ("naiixi_DisneyPlus.list", "Disney+"),
    ("HotKids_Bilibili.list", "哔哩哔哩"),
    ("HotKids_HBO_Max.list", "HBO Max"),
    ("ACL4SSR_Bahamut.list", "巴哈姆特"),
]


class RulesetStore:
    """规则集管理"""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._file = os.path.join(data_dir, "rulesets.json")
        self._rulesets = {}
        self._load()

    def _load(self):
        if os.path.exists(self._file):
            try:
                with open(self._file, encoding="utf-8") as f:
                    self._rulesets = json.load(f)
            except Exception:
                self._rulesets = {}

    def _save(self):
        with open(self._file, "w", encoding="utf-8") as f:
            json.dump(self._rulesets, f, ensure_ascii=False, indent=2)

    def builtin(self) -> List[dict]:
        """内置规则集清单"""
        return [
            {
                "id": name,
                "name": name.replace("_", " ").replace(".list", ""),
                "file": name,
                "surge_url": f"{MYRULESETS_SURGE_BASE}/{name}",
                "clash_url": f"{MYRULESETS_CLASH_BASE}/{name}",
                "description": desc,
                "builtin": True,
            }
            for name, desc in BUILTIN_RULESETS
        ]

    def list(self) -> List[dict]:
        """所有规则集（内置 + 自定义）"""
        rulesets = self.builtin()
        for rid, rs in self._rulesets.items():
            rulesets.append({
                "id": rid,
                "name": rs.get("name", rid),
                "surge_url": rs.get("surge_url", ""),
                "clash_url": rs.get("clash_url", ""),
                "description": rs.get("description", ""),
                "builtin": False,
            })
        return rulesets

    def create(self, data: dict) -> dict:
        """创建自定义规则集"""
        rid = uuid.uuid4().hex[:12]
        rs = {
            "name": data.get("name", "custom"),
            "surge_url": data.get("surge_url", ""),
            "clash_url": data.get("clash_url", ""),
            "description": data.get("description", ""),
        }
        self._rulesets[rid] = rs
        self._save()
        return {"id": rid, **rs, "builtin": False}

    def delete(self, rid: str) -> bool:
        if rid in self._rulesets:
            del self._rulesets[rid]
            self._save()
            return True
        return False
