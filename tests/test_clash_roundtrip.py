"""Clash 解析→生成 往返测试（验证复杂传输参数不丢失）。"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
from app.parsers.clash import ClashParser
from app.producers.clash import ClashProducer


def _make_clash(proxies):
    """构造 Clash YAML"""
    return yaml.dump({"proxies": proxies}, allow_unicode=True)


def test_vmess_ws_roundtrip():
    """VMess + WebSocket 传输往返"""
    src = _make_clash([{
        "name": "测试节点", "type": "vmess",
        "server": "1.2.3.4", "port": 443,
        "uuid": "abc-123", "alterId": 0, "cipher": "auto",
        "network": "ws",
        "tls": True, "servername": "example.com",
        "ws-opts": {"path": "/ws", "headers": {"Host": "example.com"}},
    }])
    nodes = ClashParser().parse(src)
    assert len(nodes) == 1
    n = nodes[0]
    assert n.protocol == "vmess"
    assert n.params.get("ws-path") == "/ws"
    assert n.params.get("host") == "example.com"
    assert n.params.get("servername") == "example.com"
    assert n.params.get("tls") is True


def test_vless_grpc_roundtrip():
    """VLESS + gRPC 传输往返"""
    src = _make_clash([{
        "name": "grpc节点", "type": "vless",
        "server": "5.6.7.8", "port": 443,
        "uuid": "xyz-456",
        "network": "grpc",
        "tls": True,
        "grpc-opts": {"grpc-service-name": "example"},
    }])
    nodes = ClashParser().parse(src)
    assert len(nodes) == 1
    n = nodes[0]
    assert n.protocol == "vless"
    assert n.params.get("grpc-service-name") == "example"


def test_hysteria2_roundtrip():
    """Hysteria2 参数往返"""
    src = _make_clash([{
        "name": "hy2节点", "type": "hysteria2",
        "server": "9.9.9.9", "port": 8443,
        "password": "pass123",
        "sni": "hy.example.com",
        "obfs": "salamander", "obfs-password": "obfs-pass",
        "up": "100 Mbps", "down": "200 Mbps",
    }])
    nodes = ClashParser().parse(src)
    assert len(nodes) == 1
    n = nodes[0]
    assert n.protocol == "hysteria2"
    assert n.params.get("obfs") == "salamander"
    assert n.params.get("up") == "100 Mbps"


def test_generate_preserves_ws():
    """生成时保留 ws-opts"""
    src = _make_clash([{
        "name": "ws节点", "type": "vmess",
        "server": "1.2.3.4", "port": 443,
        "uuid": "abc", "cipher": "auto",
        "network": "ws", "tls": True, "servername": "ex.com",
        "ws-opts": {"path": "/ws", "headers": {"Host": "ex.com"}},
    }])
    nodes = ClashParser().parse(src)
    from app.models.profile import TransformConfig
    out = ClashProducer().generate(nodes, transforms=TransformConfig())
    data = yaml.safe_load(out)
    proxy = data["proxies"][0]
    assert proxy["ws-opts"]["path"] == "/ws"
    assert proxy["tls"] is True


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v) and v.__module__ == __name__]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"✅ {t.__name__}")
            passed += 1
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"❌ {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} 通过")
