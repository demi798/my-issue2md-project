"""资源引用模型"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ResourceType(str, Enum):
    """GitHub 资源类型枚举"""

    ISSUE = "issues"
    PULL = "pulls"
    DISCUSSION = "discussions"


@dataclass(frozen=True)
class ResourceRef:
    """GitHub 资源的引用标识，解析自 URL。"""

    owner: str
    repo: str
    type: ResourceType
    number: int

    @property
    def url(self) -> str:
        """重构为完整 GitHub URL。"""
        return f"https://github.com/{self.owner}/{self.repo}/{self.type.value}/{self.number}"


__all__ = ["ResourceType", "ResourceRef"]
