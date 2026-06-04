"""Issue/PR 数据模型"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Self

from .resource import ResourceRef


@dataclass(frozen=True)
class Label:
    """Issue/PR 的标签。"""
    name: str
    color: str | None = None


@dataclass(frozen=True)
class Comment:
    """通用评论结构。"""
    author: str
    body: str
    created_at: datetime


@dataclass(frozen=True)
class IssueData:
    """Issue 或 Pull Request 的完整数据。"""
    ref: ResourceRef
    title: str
    state: str
    author: str
    body: str
    created_at: datetime
    updated_at: datetime
    labels: list[Label] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    # PR 专用字段，Issue 中为 None
    draft: bool | None = None
    merged: bool | None = None
    mergeable: bool | None = None

    @property
    def comments_count(self) -> int:
        """返回真实评论总数（用于 frontmatter）。"""
        return len(self.comments)

    @property
    def type(self) -> str:
        """返回资源类型字符串。"""
        return "issue" if self.ref.type.value == "issues" else "pull"


__all__ = ["Label", "Comment", "IssueData"]