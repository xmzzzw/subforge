"""二维码功能测试。"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.qr import generate_qr_png, is_valid_uri


def test_generate_qr_png():
    """生成二维码 PNG"""
    png = generate_qr_png("ss://YWVzLTI1Ni1nY206cGFzcw==@1.2.3.4:8388#测试")
    assert len(png) > 100
    assert png[:8] == b"\x89PNG\r\n\x1a\n"  # PNG 魔数


def test_generate_qr_png_subscription():
    """生成订阅链接二维码"""
    png = generate_qr_png("/api/subscribe?profile=flower")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_is_valid_uri():
    """URI 校验"""
    assert is_valid_uri("ss://YWVzLTI1Ni1nY206cGFzcw==@1.2.3.4:8388#name")
    assert is_valid_uri("trojan://pass@1.2.3.4:443#name")
    assert is_valid_uri("anytls://pass@1.2.3.4:443#name")
    assert is_valid_uri("https://example.com/sub")
    assert not is_valid_uri("")
    assert not is_valid_uri("not a uri")


def test_qr_different_content():
    """不同内容生成不同二维码"""
    png1 = generate_qr_png("node1")
    png2 = generate_qr_png("node2")
    assert png1 != png2


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"✅ {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"❌ {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} 通过")
