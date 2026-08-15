"""订阅聚合服务 —— 合并多个订阅，去重，透传订阅信息。

借鉴 sub-store 的聚合能力：
- 多个机场订阅合并
- 按 server:port 去重（同一节点不重复）
- 透传订阅信息（流量/到期，取第一个有数据的）
- 失败订阅容错（一个失败不影响其他）
"""
from typing import List, Optional
from ..models.node import Node
from .fetcher import fetch_subscription, SubscriptionInfo


class AggregateResult:
    """聚合结果"""

    def __init__(self):
        self.nodes: List[Node] = []
        self.info: Optional[SubscriptionInfo] = None
        self.errors: List[str] = []
        self.sources: int = 0

    @property
    def node_count(self) -> int:
        return len(self.nodes)


def aggregate_subscriptions(
    subscriptions: list,
    parse_func,
    dedup: bool = True,
) -> AggregateResult:
    """聚合多个订阅

    subscriptions: [{"url":..., "ua":..., "prefix":...}]
    parse_func: 解析函数 (content, source_type) -> List[Node]
    dedup: 是否去重（按 server:port）
    """
    result = AggregateResult()
    seen = set()

    for sub in subscriptions:
        try:
            content, info = fetch_subscription(sub.get("url"), ua=sub.get("ua"))
            nodes = parse_func(content, "auto")
            result.sources += 1

            # 订阅信息透传（取第一个有数据的）
            if result.info is None and info is not None and info.has_data:
                result.info = info

            # 节点前缀（可选，用于区分不同机场）
            prefix = sub.get("prefix", "")
            for node in nodes:
                if prefix:
                    node.name = f"{prefix} {node.name}"

                # 去重
                key = f"{node.server}:{node.port}"
                if dedup and key in seen:
                    continue
                seen.add(key)
                result.nodes.append(node)

        except Exception as e:
            result.errors.append(f"{sub.get('url', '?')}: {e}")

    return result
