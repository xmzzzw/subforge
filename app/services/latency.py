"""延迟测试服务 —— 对节点服务器端口做 TCP 连接测速。

借鉴塔台的测速思路：节点端口连接耗时作为延迟指标。
用并发线程池避免阻塞，超时控制。
"""
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict


def _test_one(server: str, port: int, timeout: float = 3.0) -> float:
    """测试单个节点延迟（毫秒），失败返回 -1"""
    try:
        start = time.time()
        sock = socket.create_connection((server, port), timeout=timeout)
        sock.close()
        elapsed = (time.time() - start) * 1000
        return round(elapsed, 1)
    except Exception:
        return -1.0


def test_latency(nodes: List[dict], timeout: float = 3.0, max_workers: int = 10) -> List[dict]:
    """并发测试节点延迟

    nodes: [{"name": ..., "server": ..., "port": ...}]
    """
    results = []
    tasks = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for node in nodes:
            future = executor.submit(_test_one, node["server"], node["port"], timeout)
            futures[future] = node

        for future in as_completed(futures):
            node = futures[future]
            latency = future.result()
            results.append({
                "name": node["name"],
                "server": node["server"],
                "port": node["port"],
                "latency": latency,
                "status": "ok" if latency >= 0 else "timeout",
            })

    # 按延迟排序（成功在前）
    results.sort(key=lambda x: (x["latency"] < 0, x["latency"]))
    return results


def summarize(results: List[dict]) -> Dict:
    """汇总延迟测试结果"""
    ok = [r for r in results if r["latency"] >= 0]
    timeout = [r for r in results if r["latency"] < 0]
    if ok:
        avg = sum(r["latency"] for r in ok) / len(ok)
        best = min(r["latency"] for r in ok)
    else:
        avg = -1
        best = -1
    return {
        "total": len(results),
        "ok": len(ok),
        "timeout": len(timeout),
        "avg_ms": round(avg, 1) if avg >= 0 else -1,
        "best_ms": round(best, 1) if best >= 0 else -1,
    }
