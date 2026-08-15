"""管道引擎 —— 核心架构：Fetch → Parse → Transform → Produce → Validate。

每阶段独立模块，可插拔、可测试。这是避免耦合的关键设计。
"""
from typing import List, Optional
from ..models.node import Node
from ..models.profile import Profile, ConvertRequest, TransformConfig


class Pipeline:
    """转换管道"""

    def __init__(self):
        self._parsers = {}
        self._transforms = []
        self._producers = {}
        self._validators = {}

    # ---- 解析器注册 ----
    def register_parser(self, name: str, parser):
        self._parsers[name] = parser

    def register_producer(self, name: str, producer):
        self._producers[name] = producer

    def register_validator(self, name: str, validator):
        self._validators[name] = validator

    def add_transform(self, transform):
        """添加转换阶段（有序）"""
        self._transforms.append(transform)

    # ---- 执行 ----
    def parse(self, content: str, source_type: str = "auto", **kwargs) -> List[Node]:
        """解析订阅内容为节点列表

        - content: 配置内容或订阅 URL
        - source_type: auto/surge/clash/uri/base64/url
        - kwargs: 可传 fetch 函数（拉取 URL 用）
        """
        if source_type == "auto":
            source_type = self._detect_source_type(content)

        # URL 类型：先拉取再解析
        if source_type == "url":
            fetch = kwargs.get("fetch") or self._default_fetch
            content, _info = fetch(content)
            source_type = "auto"
            source_type = self._detect_source_type(content)

        parser = self._parsers.get(source_type)
        if not parser:
            raise ValueError(f"不支持的来源类型: {source_type}")
        return parser.parse(content)

    @staticmethod
    def _default_fetch(url: str):
        """默认拉取（延迟导入避免循环）"""
        from ..services.fetcher import fetch_subscription
        return fetch_subscription(url)

    def transform(self, nodes: List[Node], config: TransformConfig) -> List[Node]:
        """执行转换管道"""
        result = nodes
        for transform in self._transforms:
            result = transform.apply(result, config)
        return result

    def produce(self, nodes: List[Node], target: str, **kwargs) -> str:
        """生成目标格式"""
        producer = self._producers.get(target)
        if not producer:
            raise ValueError(f"不支持的目标格式: {target}")
        return producer.generate(nodes, **kwargs)

    def validate(self, content: str, target: str) -> bool:
        """验证生成的配置"""
        validator = self._validators.get(target)
        if not validator:
            return True  # 无验证器视为通过
        return validator.validate(content)

    @staticmethod
    def _detect_source_type(content: str) -> str:
        """自动检测输入类型"""
        stripped = content.strip()
        if stripped.startswith("http://") or stripped.startswith("https://"):
            return "url"
        if stripped.startswith(("ss://", "ssr://", "trojan://", "anytls://",
                                "vmess://", "vless://", "hysteria://", "tuic://")):
            return "uri"
        if "proxies:" in content and "type:" in content:
            return "clash"
        if "[Proxy]" in content and " = " in content:
            return "surge"
        # Base64 检测
        try:
            import base64
            decoded = base64.b64decode(stripped).decode('utf-8', errors='replace')
            if "://" in decoded:
                return "base64"
        except Exception:
            pass
        return "unknown"

    # ---- 完整转换 ----
    def convert(self, request: ConvertRequest) -> dict:
        """单次转换（不保存 Profile）"""
        nodes = self.parse(request.source, request.source_type)
        nodes = self.transform(nodes, request.transforms)
        content = self.produce(nodes, request.target, transforms=request.transforms)
        valid = self.validate(content, request.target)
        return {
            "config": content,
            "nodes": len(nodes),
            "target": request.target,
            "valid": valid,
        }
