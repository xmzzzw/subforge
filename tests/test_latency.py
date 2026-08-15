"""延迟测试功能测试。"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.latency import _test_one, test_latency, summarize


def test_test_one_ok():
    """可连接节点返回延迟"""
    # 用 223.5.5.5:53（阿里 DNS，通常可达）
    latency = _test_one("223.5.5.5", 53, timeout=2)
    assert latency >= 0


def test_test_one_timeout():
    """不可达节点返回 -1"""
    latency = _test_one("192.0.2.1", 80, timeout=1)  # TEST-NET 地址不可达
    assert latency == -1


def test_latency_batch():
    """批量测试"""
    nodes = [
        {"name": "A", "server": "223.5.5.5", "port": 53},
        {"name": "B", "server": "192.0.2.1", "port": 80},
    ]
    results = test_latency(nodes, timeout=2)
    assert len(results) == 2
    # 排序后可达的在前
    assert results[0]["name"] == "A"
    assert results[0]["status"] == "ok"
    assert results[1]["name"] == "B"
    assert results[1]["status"] == "timeout"


def test_summarize():
    """汇总统计"""
    results = [
        {"latency": 100, "status": "ok"},
        {"latency": 200, "status": "ok"},
        {"latency": -1, "status": "timeout"},
    ]
    summary = summarize(results)
    assert summary["total"] == 3
    assert summary["ok"] == 2
    assert summary["timeout"] == 1
    assert summary["avg_ms"] == 150
    assert summary["best_ms"] == 100


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
