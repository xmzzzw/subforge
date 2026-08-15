"""转换历史 —— 记录最近转换操作，方便复用。

轻量实现：内存 + JSON 持久化，最多保留 MAX_ITEMS 条。
"""
import json
import os
import time
import uuid
from typing import List, Optional


class HistoryStore:
    """转换历史存储"""

    MAX_ITEMS = 20

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._file = os.path.join(data_dir, "history.json")
        self._items: List[dict] = []
        self._load()

    def _load(self):
        if os.path.exists(self._file):
            try:
                with open(self._file, encoding="utf-8") as f:
                    self._items = json.load(f)
            except Exception:
                self._items = []

    def _save(self):
        with open(self._file, "w", encoding="utf-8") as f:
            json.dump(self._items, f, ensure_ascii=False, indent=2)

    def add(self, target: str, source_type: str, node_count: int, source_preview: str = "") -> dict:
        """添加历史记录"""
        item = {
            "id": uuid.uuid4().hex[:12],
            "target": target,
            "source_type": source_type,
            "node_count": node_count,
            "source_preview": source_preview[:100],
            "timestamp": int(time.time()),
        }
        self._items.insert(0, item)
        # 限制数量
        if len(self._items) > self.MAX_ITEMS:
            self._items = self._items[:self.MAX_ITEMS]
        self._save()
        return item

    def list(self) -> List[dict]:
        return self._items

    def clear(self):
        self._items = []
        self._save()
