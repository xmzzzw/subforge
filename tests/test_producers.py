"""多格式生成器测试。"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.parsers.surge import SurgeParser
from app.transforms.group import CountryGroupBuilder
from app.models.profile import TransformConfig
from app.producers.surge import SurgeProducer
from app.producers.clash import ClashProducer
from app.producers.loon import LoonProducer
from app.producers.quanx import QuanXProducer
from app.producers.shadowrocket import ShadowrocketProducer
from app.producers.singbox import SingBoxProducer

SURGE_CONTENT = """[Proxy]
DIRECT = direct
🇭🇰 香港 01 = ss, 1.2.3.4, 10001, encrypt-method=aes-128-gcm, password=pass1, obfs=http, obfs-host=host.com
🇭🇰 香港 02 = ss, 1.2.3.4, 10002, encrypt-method=aes-128-gcm, password=pass1, obfs=http, obfs-host=host.com
🇺🇸 美国 01 = trojan, 5.6.7.8, 443, password=pass2, sni=us.example.com
"""


def _get_nodes():
    parser = SurgeParser()
    nodes = parser.parse(SURGE_CONTENT)
    builder = CountryGroupBuilder()
    config = TransformConfig()
    builder.apply(nodes, config)
    return nodes, config


def test_surge_producer():
    nodes, config = _get_nodes()
    output = SurgeProducer().generate(nodes, transforms=config)
    assert "[Proxy]" in output
    assert "[Proxy Group]" in output
    assert "[Rule]" in output
    assert "FINAL,✈️Final" in output


def test_clash_producer():
    import yaml
    nodes, config = _get_nodes()
    output = ClashProducer().generate(nodes, transforms=config)
    data = yaml.safe_load(output)
    assert len(data["proxies"]) == 3
    assert "MATCH,✈️Final" in data["rules"]


def test_loon_producer():
    nodes, config = _get_nodes()
    output = LoonProducer().generate(nodes, transforms=config)
    assert "[Proxy]" in output
    assert "[Proxy Group]" in output
    assert "[Rule]" in output


def test_quanx_producer():
    nodes, config = _get_nodes()
    output = QuanXProducer().generate(nodes, transforms=config)
    assert "[server_local]" in output
    assert "[policy]" in output
    assert "[filter_local]" in output
    assert "static=" in output  # QX 策略组格式


def test_shadowrocket_producer():
    nodes, config = _get_nodes()
    output = ShadowrocketProducer().generate(nodes, transforms=config)
    assert "[Proxy]" in output
    assert "[Proxy Group]" in output


def test_singbox_producer():
    import json
    nodes, config = _get_nodes()
    output = SingBoxProducer().generate(nodes, transforms=config)
    data = json.loads(output)
    assert data["log"]["level"] == "warn"
    assert len(data["outbounds"]) > 1  # direct + nodes


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
