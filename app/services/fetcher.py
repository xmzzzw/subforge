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

    # 绕过系统代理（关键：trust_env=False 完全忽略代理环境变量）
    # 否则 requests 即使 proxies=None 也会读 HTTPS_PROXY 等环境变量走代理，
    # 导致出口 IP 是代理 IP，被机场限制。
    if not use_proxy:
        session = requests.Session()
        session.trust_env = False
    else:
        session = requests.Session()

    # 尝试多个 UA
    uas = [ua] + [u for u in USER_AGENTS if u != ua]

    for current_ua in uas:
        headers["User-Agent"] = current_ua
        try:
            resp = session.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                text = resp.text
                stripped = text.strip()
                # 200 但内容是错误提示（窗口期/IP限制）不算成功
                if "已被限制" in stripped:
                    raise SubscriptionFetchError(
                        "机场限制了当前网络 IP。请确认使用真实网络（绕过代理），或稍后再试。"
                    )
                if "打开" in stripped and "开启" in stripped:
                    raise SubscriptionFetchError(
                        "机场有订阅时间窗口。请打开机场后台的「订阅详情」页面开启订阅获取（10分钟有效），然后再试。"
                    )
                if len(text) < 30 and ("IP" in stripped or "订阅" in stripped):
                    raise SubscriptionFetchError(
                        f"订阅返回异常: {stripped[:80]}"
                    )
                info = SubscriptionInfo.from_header(
                    resp.headers.get("subscription-userinfo")
                )
                return text, info
            elif resp.status_code in (400, 403):
                # 可能是时间窗口或 IP 限制，尝试下一个 UA
                continue
        except SubscriptionFetchError:
            raise
        except requests.RequestException:
            continue

    raise SubscriptionFetchError(
        "订阅拉取失败。可能原因：\n"
        "1. 机场有订阅时间窗口，请打开机场后台开启订阅\n"
        "2. 机场限制了当前网络 IP\n"
        "3. 订阅 URL 无效"
    )
