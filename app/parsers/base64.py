"""Base64 订阅解析器 —— 解析 Base64 编码的节点列表。"""
import base64
from typing import List
from .base import BaseParser
from .uri import URIParser
from ..models.node import Node


class Base64Parser(BaseParser):
    """解析 Base64 订阅（每行一个 URI）"""

    name = "base64"

    def __init__(self):
        self._uri_parser = URIParser()

    def parse(self, content: str) -> List[Node]:
        # 尝试解码 Base64
        decoded = self._try_decode(content)
        if decoded is None:
            return []
        return self._uri_parser.parse(decoded)

    @staticmethod
    def _try_decode(content: str) -> str | None:
        stripped = content.strip()
        # 处理可能带前缀的 base64
        try:
            decoded = base64.b64decode(stripped).decode('utf-8', errors='replace')
            # 解码后应包含协议 URI
            if "://" in decoded:
                return decoded
        except Exception:
            pass
        return None
