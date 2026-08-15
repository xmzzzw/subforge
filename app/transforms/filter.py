"""节点筛选 —— 根据 include/exclude 关键词过滤节点。"""
import re
from typing import List
from ..models.node import Node
from ..models.profile import TransformConfig


class NodeFilter:
    """按关键词筛选节点"""

    def apply(self, nodes: List[Node], config: TransformConfig) -> List[Node]:
        result = nodes
        if config.include:
            result = [n for n in result if self._match_any(n, config.include)]
        if config.exclude:
            result = [n for n in result if not self._match_any(n, config.exclude)]
        return result

    @staticmethod
    def _match_any(node: Node, keywords: List[str]) -> bool:
        """节点名或国家匹配任一关键词"""
        text = f"{node.name} {node.country or ''} {node.server}"
        return any(kw.lower() in text.lower() for kw in keywords)
