"""国家分组构建 —— 生成统一规格的策略组结构。

规格（用户要求）:
    Proxies → 应用组(AI/Netflix/...) → 🎯Direct → ✈️Final → 国家分组 + 自动选择
"""
from typing import List, Tuple
from ..models.node import Node
from ..models.profile import TransformConfig
from ..core.country import group_by_country, merge_singletons


class CountryGroupBuilder:
    """构建国家分组的转换器"""

    # 应用策略组（固定顺序）
    APP_GROUPS = [
        "AI", "Netflix", "HBO", "DisneyPlus", "YouTube", "Bahamut",
        "Bilibili", "MyTVSuper", "Telegram", "Crypto", "Steam", "Epic",
        "Xbox", "PlayStation", "Microsoft", "Scholar", "Apple", "Google", "Tiktok",
    ]

    TEST_URL = "http://www.gstatic.com/generate_204"

    def apply(self, nodes: List[Node], config: TransformConfig) -> List[Node]:
        """核心转换：给节点打上国家标签 + 协议标注"""
        # 1. 国家识别（每个节点）
        for node in nodes:
            if not node.country:
                from ..core.country import detect_country
                node.country = detect_country(node.name)

        # 2. 协议标注
        if config.protocol_tag:
            for node in nodes:
                node.tag = f"[{node.protocol}]"

        return nodes

    def build_groups(self, nodes: List[Node], config: TransformConfig) -> List[dict]:
        """构建策略组定义（供各生成器使用）"""
        groups = []

        # 按国家分组
        by_country = group_by_country(nodes)
        if config.merge_single:
            by_country = merge_singletons(by_country, threshold=1)

        # 排序（多节点优先）
        countries = sorted(by_country.keys(), key=lambda x: -len(by_country[x]))

        # 顶层 Proxies
        groups.append({"name": "Proxies", "type": "select", "members": countries})

        # 应用策略组
        for app in self.APP_GROUPS:
            groups.append({
                "name": app, "type": "select",
                "members": ["Proxies", "🎯Direct"] + countries,
            })

        # 直连 + Final
        groups.append({"name": "🎯Direct", "type": "select",
                       "members": ["DIRECT", "Proxies"]})
        groups.append({"name": "✈️Final", "type": "select",
                       "members": ["Proxies", "🎯Direct"] + countries})

        # 国家分组 + 自动选择（放 Final 后面）
        for c in countries:
            names = [n.tagged_name() for n in by_country[c]]
            auto = f"{c}-自动"
            if config.auto_select:
                groups.append({"name": c, "type": "select",
                               "members": [auto] + names})
                groups.append({"name": auto, "type": "url-test",
                               "members": names,
                               "url": self.TEST_URL, "interval": 300, "tolerance": 50})
            else:
                groups.append({"name": c, "type": "select", "members": names})

        return groups, by_country
