"""Markdown 转换模块"""

import yaml
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from ..models.issue import IssueData
from ..models.discussion import DiscussionData

if TYPE_CHECKING:
    from ..models.resource import ResourceRef


def render_frontmatter(data: IssueData | DiscussionData) -> str:
    """生成 YAML frontmatter。

    Args:
        data: IssueData 或 DiscussionData 对象

    Returns:
        YAML frontmatter 字符串
    """
    # 构建基础数据
    frontmatter = {
        "url": data.ref.url,
        "type": data.type,
        "owner": data.ref.owner,
        "repo": data.ref.repo,
        "number": data.ref.number,
        "title": data.title,
        "author": data.author,
        "created_at": data.created_at.isoformat(),
        "updated_at": data.updated_at.isoformat(),
        "labels": [label.name for label in data.labels],
        "comments_count": data.comments_count,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }

    # 添加特定字段的扩展
    if isinstance(data, IssueData):
        frontmatter["state"] = data.state
    elif isinstance(data, DiscussionData):
        # Discussion 没有 state 字段，使用默认值 "open"
        frontmatter["state"] = "open"

    # 添加特定字段的扩展
    if isinstance(data, IssueData):
        if data.draft is not None:
            frontmatter["draft"] = data.draft
        if data.merged is not None:
            frontmatter["merged"] = data.merged
        if data.mergeable is not None:
            frontmatter["mergeable"] = data.mergeable
    elif isinstance(data, DiscussionData):
        frontmatter["category"] = data.category
        frontmatter["answer_chosen"] = data.answer_chosen

    # 生成 YAML 字符串
    return yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)


def render_body(data: IssueData | DiscussionData, max_comments: int = 0) -> str:
    """渲染 Markdown 正文。

    Args:
        data: IssueData 或 DiscussionData 对象
        max_comments: 限制评论数量（0 表示不限制）

    Returns:
        Markdown 正文字符串
    """
    # 准备评论列表
    all_comments = data.comments

    # 应用评论数量限制
    if max_comments > 0:
        display_comments = all_comments[:max_comments]
    else:
        display_comments = all_comments

    # 构建标题
    title = data.title
    if isinstance(data, IssueData):
        state = data.state
        if state == "merged":
            title = f"{title}  [merged]"
        else:
            title = f"{title}  [{state}]"
    else:
        # Discussion 没有 state 字段，使用默认值 "open"
        title = f"{title}  [open]"

    body_parts = [f"# {title}\n"]
    body_parts.append(f"\n{data.body}\n")
    body_parts.append("\n---\n")

    # 添加评论部分
    if display_comments:
        body_parts.append(f"\n## Comments ({len(display_comments)})\n")

        for i, comment in enumerate(display_comments, 1):
            # 格式化时间
            created_at = comment.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            body_parts.append(f"\n### Comment {i} — @{comment.author} · {created_at}\n")
            body_parts.append(f"\n{comment.body}\n")
    else:
        body_parts.append("\n## Comments (0)\n")

    return "".join(body_parts)


def render(data: IssueData | DiscussionData, max_comments: int = 0) -> str:
    """渲染完整的 Markdown 文件内容。

    Args:
        data: IssueData 或 DiscussionData 对象
        max_comments: 限制评论数量（0 表示不限制）

    Returns:
        完整的 Markdown 内容（frontmatter + 正文）
    """
    # 生成 frontmatter
    frontmatter = render_frontmatter(data)

    # 生成正文
    body = render_body(data, max_comments)

    # 组合完整内容
    return f"---\n{frontmatter}---\n{body}"


__all__ = ["render_frontmatter", "render_body", "render"]
