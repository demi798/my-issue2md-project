"""Discussion 数据模型"""

from dataclasses import dataclass, field
from datetime import datetime

from .resource import ResourceRef
from .issue import Comment, Label


@dataclass(frozen=True)
class DiscussionData:
    """Discussion 的完整数据。"""
    ref: ResourceRef
    title: str
    author: str
    body: str
    created_at: datetime
    updated_at: datetime
    category: str
    labels: list[Label] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    answer_chosen: bool = False

    @property
    def comments_count(self) -> int:
        """返回真实评论总数（用于 frontmatter）。"""
        return len(self.comments)

    @property
    def type(self) -> str:
        """返回资源类型字符串。"""
        return "discussion"


__all__ = ["DiscussionData"]