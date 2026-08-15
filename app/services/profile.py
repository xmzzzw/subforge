"""配置档案管理 —— Profile 持久化（JSON 文件）。

一个 Profile 定义一个「输入订阅 + 转换规则 + 输出格式」的完整配置。
"""
import json
import os
import uuid
from typing import Dict, List, Optional
from ..models.profile import Profile


class ProfileStore:
    """Profile 存储（JSON 文件）"""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._file = os.path.join(data_dir, "profiles.json")
        self._profiles: Dict[str, Profile] = {}
        self._load()

    def _load(self):
        if os.path.exists(self._file):
            try:
                with open(self._file, encoding="utf-8") as f:
                    data = json.load(f)
                for pid, p in data.items():
                    self._profiles[pid] = Profile(**p)
            except Exception:
                self._profiles = {}

    def _save(self):
        data = {pid: p.model_dump() for pid, p in self._profiles.items()}
        with open(self._file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list(self) -> List[Profile]:
        return list(self._profiles.values())

    def get(self, profile_id: str) -> Optional[Profile]:
        return self._profiles.get(profile_id)

    def get_by_name(self, name: str) -> Optional[Profile]:
        for p in self._profiles.values():
            if p.name == name:
                return p
        return None

    def create(self, profile: Profile) -> Profile:
        if not profile.id:
            profile.id = uuid.uuid4().hex[:12]
        self._profiles[profile.id] = profile
        self._save()
        return profile

    def update(self, profile_id: str, profile: Profile) -> Optional[Profile]:
        if profile_id not in self._profiles:
            return None
        profile.id = profile_id
        self._profiles[profile_id] = profile
        self._save()
        return profile

    def delete(self, profile_id: str) -> bool:
        if profile_id in self._profiles:
            del self._profiles[profile_id]
            self._save()
            return True
        return False
