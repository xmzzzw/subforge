"""二维码生成服务 —— 支持节点 URI 和订阅链接二维码。

用法：
- 节点二维码: 把节点 URI (ss:// trojan:// anytls:// ...) 渲染成 PNG
- 订阅二维码: 把 subforge 订阅链接渲染成 PNG（手机扫码导入整个订阅）

借鉴塔台：correctionLevel = "M"（纠错等级 M）
"""
import io
from typing import Optional

import qrcode
from qrcode.image.pil import PilImage

# 订阅/节点 URL 前缀白名单（防止二维码被滥用）
ALLOWED_PREFIXES = (
    "ss://", "ssr://", "trojan://", "anytls://", "vmess://", "vless://",
    "hysteria://", "hysteria2://", "tuic://", "wireguard://", "socks5://",
    "http://", "https://",
)


def generate_qr_png(content: str, box_size: int = 12, border: int = 4) -> bytes:
    """生成二维码 PNG 字节流"""
    qr = qrcode.QRCode(
        version=None,  # 自动
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(content)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def is_valid_uri(uri: str) -> bool:
    """校验是否为合法的订阅/节点 URI"""
    uri = uri.strip()
    return uri.startswith(ALLOWED_PREFIXES) and len(uri) > 10
