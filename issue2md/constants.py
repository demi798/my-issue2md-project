"""issue2md 运行时配置常量"""

from __future__ import annotations

# 限流重试最大等待时间（秒），超过则不再等待
MAX_RETRY_WAIT_SECONDS = 600

__all__ = ["MAX_RETRY_WAIT_SECONDS"]
