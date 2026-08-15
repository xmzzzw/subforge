"""解析器基类。"""
from abc import ABC, abstractmethod
from typing import List
from ..models.node import Node


class BaseParser(ABC):
    """解析器基类：把各种格式的订阅解析为统一 Node 列表"""

    name: str = "base"

    @abstractmethod
    def parse(self, content: str) -> List[Node]:
        """解析内容为节点列表"""
        raise NotImplementedError
