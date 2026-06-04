"""GitHub API 客户端（REST + GraphQL）。

本模块的职责边界（单一职责原则）：
- 输入：``ResourceRef`` + 可选 Token。
- 输出：标准化的 ``IssueData`` / ``PRData`` / ``DiscussionData`` 数据结构。
- **不**负责 Markdown 渲染、文件写入或 CLI 编排。

为何混合 REST + GraphQL
------------------------
- Issue / PR 走 REST API v3：成熟稳定、分页简单。
- Discussion **只能**走 GraphQL API v4（REST 不暴露）。

鉴权策略（spec.md §1.3）
------------------------
优先级：``--token`` 参数 > ``GITHUB_TOKEN`` 环境变量 > 匿名调用。
匿名调用受 60 次/小时限流，超限时由本模块触发等待重试逻辑。

限流处理（spec.md §1.4.1）
--------------------------
收到 ``X-RateLimit-Remaining: 0`` 时：
1. 读取 ``X-RateLimit-Reset`` 头计算等待秒数。
2. 若 ≤ 600 秒，stderr 打印提示后 sleep + 重试一次。
3. 仍失败抛出 :class:`RateLimitError`。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable

from .errors import AuthError, GithubAPIError, RateLimitError
from .parser import ResourceRef, ResourceType


# ---------------------------------------------------------------------------
# 数据结构（GitHub API 返回值的标准表示）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Comment:
    """GitHub 评论的标准化表示。"""

    author: str
    body: str
    created_at: datetime


@dataclass(frozen=True)
class Label:
    """GitHub 标签的最小化表示。"""

    name: str
    color: str | None = None


@dataclass(frozen=True)
class IssueData:
    """Issue / PR 通用数据结构。

    PR 专用字段（``draft`` / ``merged`` / ``mergeable``）以 ``None`` 表示
    在 Issue 上下文中不可用。这种"共用一个数据类"的设计选择，是为了
    避免 Issue/PR 两套并行结构带来的渲染层分支膨胀。
    """

    ref: ResourceRef
    title: str
    state: str  # open | closed | merged
    author: str
    body: str
    created_at: datetime
    updated_at: datetime
    labels: list[Label] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)

    # PR 专用字段，Issue 中保持 None
    draft: bool | None = None
    merged: bool | None = None
    mergeable: bool | None = None


@dataclass(frozen=True)
class DiscussionData:
    """Discussion 数据结构。

    Discussion 走 GraphQL，字段结构与 Issue 差异较大（有 category、
    可能有 chosen answer），因此独立定义而非复用 ``IssueData``。
    """

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


# ---------------------------------------------------------------------------
# 对外主接口（CLI 层只调这两个函数）
# ---------------------------------------------------------------------------


def fetch(ref: ResourceRef, token: str | None = None) -> IssueData | DiscussionData:
    """根据资源引用拉取完整数据（含全量评论）。

    根据 ``ref.type`` 自动路由到 REST 或 GraphQL：
    - ``ISSUE`` / ``PULL`` → REST API v3
    - ``DISCUSSION`` → GraphQL API v4

    Args:
        ref: 已解析的资源引用。
        token: 可选 GitHub Token。``None`` 时走匿名。

    Returns:
        ``IssueData`` 或 ``DiscussionData``。

    Raises:
        AuthError: Token 无效或权限不足（401/403 非限流）。
        RateLimitError: 限流且等待重试后仍失败。
        GithubAPIError: 其它 HTTP/网络错误（404、5xx、超时）。
    """
    raise NotImplementedError("待 TDD 实现")


def validate_token(token: str) -> None:
    """校验 Token 格式（仅本地格式校验，不发请求）。

    规则：非空、长度 ≥ 20、仅含 ASCII 可见字符。
    更严格的"是否真的有效"由实际 API 调用隐式验证。

    Args:
        token: 待校验的 Token 字符串。

    Raises:
        AuthError: Token 格式不合法。
    """
    raise NotImplementedError("待 TDD 实现")


# ---------------------------------------------------------------------------
# 内部辅助（仅供本模块使用，不导出）
# ---------------------------------------------------------------------------


def _paginate_rest(
    url: str,
    token: str | None,
) -> Iterable[dict]:
    """REST API 分页迭代器（内部使用）。

    按 ``Link`` header 自动翻页，``per_page=100``。
    """
    raise NotImplementedError("待 TDD 实现")


def _handle_rate_limit(response_headers: dict) -> None:
    """检查响应是否触发限流，必要时 sleep 等待。

    被本模块其它 HTTP 调用复用。
    """
    raise NotImplementedError("待 TDD 实现")
