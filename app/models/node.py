"""统一节点模型 —— 所有协议解析后的标准结构。

关键设计：所有解析器输出 Node，所有生成器消费 Node，
解析新协议和生成新格式互不影响。
"""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class Node(BaseModel):
    """统一节点模型"""

    name: str
    protocol: str  # ss/trojan/anytls/vmess/vless/hysteria2/tuic/wireguard/...
    server: str
    port: int
    params: Dict[str, Any] = Field(default_factory=dict)  # 协议特定参数
    country: Optional[str] = None  # 识别出的国家（如 "🇭🇰 香港"）
    tag: Optional[str] = None  # 协议标注（如 "[ss]"）

    def tagged_name(self) -> str:
        """带协议标注的节点名"""
        if self.tag:
            return f"{self.name} {self.tag}"
        return self.name

    def country_key(self) -> str:
        """用于分组的国家键"""
        return self.country or "🌍 其他地区"

    def to_uri(self) -> str:
        """转成 URI 形式（用于分享/导入）"""
        if self.protocol == "ss":
            import base64
            cfg = f"{self.params.get('cipher', 'aes-256-gcm')}:{self.params.get('password', '')}"
            enc = base64.b64encode(cfg.encode()).decode()
            return f"ss://{enc}@{self.server}:{self.port}#{self.name}"
        elif self.protocol == "trojan":
            return f"trojan://{self.params.get('password', '')}@{self.server}:{self.port}#{self.name}"
        elif self.protocol == "anytls":
            return f"anytls://{self.params.get('password', '')}@{self.server}:{self.port}#{self.name}"
        return f"{self.protocol}://{self.server}:{self.port}#{self.name}"

    def __str__(self):
        return f"<Node {self.tagged_name()} [{self.protocol}] {self.server}:{self.port}>"
