"""生成器基类。"""
from abc import ABC, abstractmethod
from typing import List
from ..models.node import Node


class BaseProducer(ABC):
    """生成器基类：把节点列表生成目标格式配置"""

    name: str = "base"

    @abstractmethod
    def generate(self, nodes: List[Node], **kwargs) -> str:
        """生成配置"""
        raise NotImplementedError
