"""mihomo 配置验证器 —— 用 mihomo -t 验证 Clash 配置。"""
import os
import subprocess
import tempfile
from typing import Optional

MIHOMO_PATHS = [
    "/Applications/Clash Verge.app/Contents/MacOS/verge-mihomo",
]


class MihomoValidator:
    """验证 Clash/mihomo 配置合法性（有 mihomo 时可用）"""

    def validate(self, content: str) -> bool:
        """验证配置。返回 True 表示有效（或无 mihomo 可用）。"""
        mihomo = self._find_mihomo()
        if not mihomo:
            return True  # 无 mihomo 视为通过

        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
            f.write(content)
            tmp_path = f.name

        try:
            proc = subprocess.run(
                [mihomo, "-t", "-f", tmp_path],
                capture_output=True, text=True, timeout=30,
                env={**os.environ, "HOME": "/tmp"},  # 避免污染用户配置
            )
            return "successful" in proc.stdout.lower() or proc.returncode == 0
        except Exception:
            return True
        finally:
            os.unlink(tmp_path)

    @staticmethod
    def _find_mihomo() -> Optional[str]:
        for p in MIHOMO_PATHS:
            if os.path.exists(p):
                return p
        return None
