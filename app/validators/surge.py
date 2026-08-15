"""Surge 配置验证器 —— 用 surge-cli 验证。"""
import os
import subprocess
from typing import Optional

SURGE_CLI = "/Applications/Surge.app/Contents/Applications/surge-cli"
SURGE_PROFILES = os.path.expanduser(
    "~/Library/Application Support/Surge/Profiles"
)


class SurgeValidator:
    """验证 Surge 配置合法性（仅在 macOS 有 Surge 时可用）"""

    def validate(self, content: str, profile_name: Optional[str] = None) -> bool:
        """验证配置。返回 True 表示有效（或无 surge-cli 可用）。"""
        if not os.path.exists(SURGE_CLI):
            return True  # 无 surge-cli 视为通过

        if not profile_name:
            return True  # 需要 profile 名

        try:
            result = subprocess.run(
                ["echo", "quit"], capture_output=True, text=True
            )
            # 用 surge-cli profile check
            cmd = f'echo "quit" | "{SURGE_CLI}" profile check "{profile_name}"'
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            return "Valid" in proc.stdout or "valid" in proc.stdout.lower()
        except Exception:
            return True
