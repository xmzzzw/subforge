"""订阅聚合测试。"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app.services.aggregator as agg
from app.parsers.surge import SurgeParser


SURGE1 = """[Proxy]
香港01 = ss, 1.2.3.4, 10001, encrypt-method=aes-128-gcm, password=p1
香港02 = ss, 1.2.3.4, 10002, encrypt-method=aes-128-gcm, password=p1
"""

SURGE2 = """[Proxy]
香港01 = ss, 1.2.3.4, 10001, encrypt-method=aes-128-gcm, password=p1
美国01 = trojan, 5.6.7.8, 443, password=p2
"""


def _fake_fetch(url, ua=None):
    """模拟订阅拉取"""
    if url == "sub1":
        return SURGE1, None
    if url == "sub2":
        return SURGE2, None
    raise Exception("subscribe failed")


def test_aggregate_dedup():
    """聚合去重：两个订阅有相同节点只保留一个"""
    original = agg.fetch_subscription
    agg.fetch_subscription = _fake_fetch
    try:
        result = agg.aggregate_subscriptions(
            [{"url": "sub1", "ua": "test"}, {"url": "sub2", "ua": "test"}],
            lambda content, st: SurgeParser().parse(content),
            dedup=True,
        )
        # 香港01 去重，香港02 + 美国01 保留
        assert result.node_count == 3, f"节点数: {result.node_count}"
        assert result.sources == 2
        assert not result.errors
    finally:
        agg.fetch_subscription = original


def test_aggregate_prefix():
    """节点前缀：区分不同机场"""
    original = agg.fetch_subscription
    agg.fetch_subscription = _fake_fetch
    try:
        result = agg.aggregate_subscriptions(
            [{"url": "sub1", "ua": "test", "prefix": "[机场A]"}],
            lambda content, st: SurgeParser().parse(content),
            dedup=True,
        )
        assert result.node_count == 2
        assert result.nodes[0].name.startswith("[机场A]")
    finally:
        agg.fetch_subscription = original


def test_aggregate_error_tolerance():
    """失败订阅容错：一个失败不影响其他"""
    original = agg.fetch_subscription
    agg.fetch_subscription = _fake_fetch
    try:
        result = agg.aggregate_subscriptions(
            [
                {"url": "sub1", "ua": "test"},
                {"url": "bad", "ua": "test"},  # 会失败
                {"url": "sub2", "ua": "test"},
            ],
            lambda content, st: SurgeParser().parse(content),
            dedup=True,
        )
        assert result.node_count >= 2
        assert len(result.errors) == 1
    finally:
        agg.fetch_subscription = original


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
            print(f"❌ {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} 通过")
