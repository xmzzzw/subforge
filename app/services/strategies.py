"""策略组方案管理 —— 内置多套方案 + 自定义导入。

每个方案是一组策略组定义（类似塔台的内置方案）：
- myrulesets：默认标准方案（国家分组 + 应用组 + Final）
- tower-style：常用分流方案（节点选择/自动选择/AI服务等，参考塔台分流理念）
- custom：用户自定义导入
"""
import json
import os
import uuid
from typing import List, Optional


# ============ 内置方案 ============
# 策略组用占位符 {countries} / {apps} 表示引用国家分组和应用组，
# 生成时替换为实际的节点/国家
BUILTIN_STRATEGIES = [
    {
        "name": "标准方案",
        "key": "myrulesets",
        "builtin": True,
        "description": "国家分组 + 应用策略组 + 自动选择（my-rulesets 规格）",
        "groups": [
            {"name": "Proxies", "type": "select", "members": ["{countries}"]},
            {"name": "AI", "type": "select", "members": ["Proxies", "🎯Direct", "{countries}"]},
            {"name": "Netflix", "type": "select", "members": ["Proxies", "🎯Direct", "{countries}"]},
            {"name": "YouTube", "type": "select", "members": ["Proxies", "🎯Direct", "{countries}"]},
            {"name": "Telegram", "type": "select", "members": ["Proxies", "🎯Direct", "{countries}"]},
            {"name": "🎯Direct", "type": "select", "members": ["DIRECT", "Proxies"]},
            {"name": "✈️Final", "type": "select", "members": ["Proxies", "🎯Direct", "{countries}"]},
        ],
    },
    {
        "name": "常用分流方案",
        "key": "tower-style",
        "builtin": True,
        "description": "常用分流：节点选择/自动选择/AI服务/媒体/国内/国际等",
        "groups": [
            {"name": "🚀 节点选择", "type": "select", "members": ["{countries}"]},
            {"name": "♻️ 自动选择", "type": "url-test", "members": ["{auto_countries}"], "url": "http://www.gstatic.com/generate_204", "interval": 300},
            {"name": "🤖 AI 服务", "type": "select", "members": ["🚀 节点选择", "🎯Direct", "{countries}"]},
            {"name": "🎬 国外媒体", "type": "select", "members": ["🚀 节点选择", "🎯Direct", "{countries}"]},
            {"name": "📺 YouTube", "type": "select", "members": ["🚀 节点选择", "{countries}"]},
            {"name": "💬 Telegram", "type": "select", "members": ["🚀 节点选择", "{countries}"]},
            {"name": "🇨🇳 国内流量", "type": "select", "members": ["DIRECT", "🚀 节点选择"]},
            {"name": "🌐 国际流量", "type": "select", "members": ["🚀 节点选择", "🎯Direct"]},
            {"name": "🍎 苹果服务", "type": "select", "members": ["DIRECT", "🚀 节点选择"]},
            {"name": "Ⓜ️ 微软服务", "type": "select", "members": ["🚀 节点选择", "🎯Direct"]},
            {"name": "🔍 谷歌服务", "type": "select", "members": ["🚀 节点选择", "🎯Direct"]},
            {"name": "🚫 广告拦截", "type": "select", "members": ["REJECT", "DIRECT"]},
            {"name": "🎯 全球直连", "type": "select", "members": ["DIRECT"]},
            {"name": "✈️ Final", "type": "select", "members": ["🚀 节点选择", "🎯Direct", "{countries}"]},
        ],
    },
    {
        "name": "精简方案",
        "key": "minimal",
        "builtin": True,
        "description": "最小化：节点选择 + 直连 + Final",
        "groups": [
            {"name": "Proxies", "type": "select", "members": ["{countries}"]},
            {"name": "🎯Direct", "type": "select", "members": ["DIRECT", "Proxies"]},
            {"name": "✈️Final", "type": "select", "members": ["Proxies", "🎯Direct"]},
        ],
    },
]


class StrategyStore:
    """策略组方案存储"""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._file = os.path.join(data_dir, "strategies.json")
        self._custom = {}
        self._load()

    def _load(self):
        if os.path.exists(self._file):
            try:
                with open(self._file, encoding="utf-8") as f:
                    self._custom = json.load(f)
            except Exception:
                self._custom = {}

    def _save(self):
        with open(self._file, "w", encoding="utf-8") as f:
            json.dump(self._custom, f, ensure_ascii=False, indent=2)

    def list(self) -> List[dict]:
        """所有方案（内置 + 自定义）"""
        strategies = [dict(s) for s in BUILTIN_STRATEGIES]
        for sid, s in self._custom.items():
            strategies.append({**s, "id": sid, "builtin": False})
        return strategies

    def get(self, key: str) -> Optional[dict]:
        """获取方案（支持内置 key 或自定义 id）"""
        for s in BUILTIN_STRATEGIES:
            if s["key"] == key:
                return {**s, "builtin": True}
        if key in self._custom:
            return {**self._custom[key], "id": key, "builtin": False}
        return None

    def create(self, data: dict) -> dict:
        """创建自定义方案"""
        sid = uuid.uuid4().hex[:12]
        s = {
            "name": data.get("name", "自定义方案"),
            "description": data.get("description", ""),
            "groups": data.get("groups", []),
        }
        self._custom[sid] = s
        self._save()
        return {**s, "id": sid, "builtin": False}

    def delete(self, sid: str) -> bool:
        if sid in self._custom:
            del self._custom[sid]
            self._save()
            return True
        return False
