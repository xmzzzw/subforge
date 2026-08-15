"""订阅拉取服务 —— 处理机场常见限制（IP限制/时间窗口/UA）。

关键经验（来自实际踩坑）：
1. 机场常限制代理 IP，必须直连（绕过本机代理）
2. 部分机场有订阅时间窗口（需打开后台开启，10分钟有效）
3. 需要合适的 User-Agent
4. subscription-userinfo 头含流量/到期信息
"""
import requests
from typing import Optional, Tuple

DEFAULT_UA = "ClashForWindows/0.20.39"
USER_AGENTS = [
    "ClashForWindows/0.20.39",
    "Surge",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
]


class SubscriptionFetchError(Exception):
    """订阅拉取失败"""


class SubscriptionInfo:
    """订阅元信息（流量/到期等）"""

    def __init__(self):
        self.upload: Optional[int] = None
        self.download: Optional[int] = None
        self.total: Optional[int] = None
        self.expire: Optional[int] = None
        self.raw: Optional[str] = None

    @classmethod
    def from_header(cls, value: Optional[str]) -> "SubscriptionInfo":
        info = cls()
        if not value:
            return info
        info.raw = value
        for item in value.split(";"):
            item = item.strip()
            if "=" in item:
                k, _, v = item.partition("=")
                try:
                    setattr(info, k.strip(), int(v))
                except (ValueError, AttributeError):
                    pass
        return info

    @property
    def has_data(self) -> bool:
        return self.total is not None and self.total > 0


def fetch_subscription(
    url: str,
    ua: str = DEFAULT_UA,
    timeout: int = 30,
    use_proxy: bool = False,
) -> Tuple[str, SubscriptionInfo]:
    """拉取订阅内容，返回 (内容, 订阅信息)

    默认直连（绕过代理），适配机场 IP 限制。
    """
    headers = {"User-Agent": ua}

    proxies = None
    if not use_proxy:
        proxies = {"http": None, "https": None}  # 绕过系统代理

    # 尝试多个 UA
    uas = [ua] + [u for u in USER_AGENTS if u != ua]

    for current_ua in uas:
        headers["User-Agent"] = current_ua
        try:
            resp = requests.get(url, headers=headers, timeout=timeout, proxies=proxies)
            if resp.status_code == 200:
                info = SubscriptionInfo.from_header(
                    resp.headers.get("subscription-userinfo")
                )
                return resp.text, info
            elif resp.status_code in (400, 403):
                # 可能是时间窗口或 IP 限制，尝试下一个 UA
                continue
        except requests.RequestException:
            continue

    raise SubscriptionFetchError(
        "订阅拉取失败。可能原因：\n"
        "1. 机场有订阅时间窗口，请打开机场后台开启订阅\n"
        "2. 机场限制了当前网络 IP\n"
        "3. 订阅 URL 无效"
    )
