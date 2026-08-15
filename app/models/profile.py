"""配置档案模型 —— 一个 Profile 定义「输入订阅 + 转换规则 + 输出格式」。"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Subscription(BaseModel):
    """机场订阅"""

    url: str
    name: Optional[str] = None
    ua: Optional[str] = "ClashForWindows/0.20.39"  # User-Agent
    refresh_mode: str = "proxy"  # proxy（代理模式）/ snapshot（快照模式）


class TransformConfig(BaseModel):
    """转换管道配置"""

    include: Optional[List[str]] = None  # 只保留匹配的节点（关键词）
    exclude: Optional[List[str]] = None  # 排除匹配的节点
    merge_single: bool = True  # 单节点国家合并到其他地区
    protocol_tag: bool = True  # 节点名加协议标注
    country_groups: bool = True  # 生成国家分组
    auto_select: bool = True  # 国家分组带自动选择


class RuleConfig(BaseModel):
    """规则集配置"""

    mode: str = "myrulesets"  # myrulesets / custom / none
    custom_urls: List[str] = Field(default_factory=list)  # 自定义规则集 URL
    custom_rules: List[str] = Field(default_factory=list)  # 自定义规则行


class Profile(BaseModel):
    """完整配置档案"""

    id: Optional[str] = None
    name: str
    subscriptions: List[Subscription] = Field(default_factory=list)
    transforms: TransformConfig = Field(default_factory=TransformConfig)
    target: str = "clash"  # surge/clash/mihomo/loon/quanx/shadowrocket/singbox
    rules: RuleConfig = Field(default_factory=RuleConfig)
    update_interval: int = 86400  # 秒


class ConvertRequest(BaseModel):
    """单次转换请求（不保存 Profile）"""

    source: str  # 订阅 URL 或配置内容
    source_type: str = "auto"  # auto/url/surge/clash/base64/uri
    target: str = "clash"
    transforms: TransformConfig = Field(default_factory=TransformConfig)
