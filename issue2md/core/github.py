"""GitHub API 交互模块 - 先生成空函数签名供测试编译通过"""

import re
import sys
import time
from typing import TYPE_CHECKING
from datetime import datetime, timezone

import requests
from requests import Response
from ..models.resource import ResourceRef, ResourceType
from ..errors import AuthError, RateLimitError, GithubAPIError

import dateutil.parser

if TYPE_CHECKING:
    from ..models.issue import IssueData
    from ..models.discussion import DiscussionData


def validate_token(token: str) -> None:
    """验证 GitHub Token 格式。

    Args:
        token: GitHub Token 字符串

    Raises:
        AuthError: Token 格式不合法时抛出
    """
    # 检查空字符串或空白字符
    if not token or not token.strip():
        raise AuthError("Token 不能为空")

    # 检查长度（至少 20 字符）
    if len(token) < 20:
        raise AuthError("Token 长度必须至少 20 个字符")

    # 可选：验证 Token 格式（个人访问令牌以 ghp_ 开头，但不强制）
    # 这里只做基本验证，不强制要求 ghp_ 前缀
    token_pattern = re.compile(r'^[a-zA-Z0-9_\-]+$')
    if not token_pattern.match(token):
        raise AuthError("Token 包含非法字符")


def _handle_response(response, token: str | None) -> None:
    """处理 HTTP 响应，抛出语义化异常。

    Args:
        response: requests.Response 对象
        token: GitHub Token（用于错误信息）

    Raises:
        AuthError: 401 或 403 错误（非限流）
        RateLimitError: 触发限流且重试时间过长
        GithubAPIError: 其他 API 错误
    """
    # 检查限流
    remaining = int(response.headers.get("X-RateLimit-Remaining", "1"))

    if remaining == 0:
        # 限流处理
        reset_ts = int(response.headers.get("X-RateLimit-Reset", "0"))
        current_time = int(time.time())
        wait_seconds = reset_ts - current_time

        if wait_seconds > 600:  # 超过 10 分钟
            raise RateLimitError(f"Rate limit reset too far in future: {wait_seconds}s")

        if wait_seconds > 0:
            print(f"[INFO] rate-limited, waiting {wait_seconds}s until reset...", file=sys.stderr)
            time.sleep(wait_seconds)

        # 重试标记，由调用者实现重试逻辑
        return

    # 处理 HTTP 状态码
    status_code = response.status_code

    if status_code == 401:
        raise AuthError("Invalid token")
    elif status_code == 403:
        # 检查是否是限流导致的 403
        if "X-RateLimit-Remaining" in response.headers and int(response.headers["X-RateLimit-Remaining"]) == 0:
            raise RateLimitError("Rate limit exceeded")
        else:
            raise AuthError("Insufficient permissions")
    elif status_code == 404:
        raise GithubAPIError("Resource not found")
    elif status_code >= 500:
        raise GithubAPIError(f"GitHub server error: {status_code}")
    elif not response.ok:
        raise GithubAPIError(f"Unexpected status: {status_code}")


def fetch(ref: ResourceRef, token: str | None = None) -> "IssueData | DiscussionData":
    """根据资源引用拉取完整数据（含全量评论，自动分页）。

    Args:
        ref: 资源引用
        token: GitHub Token

    Returns:
        IssueData 或 DiscussionData

    Raises:
        GithubAPIError: API 调用失败时抛出
        RateLimitError: 触发限流且重试失败时抛出
        AuthError: Token 无效时抛出
    """
    from urllib.parse import parse_qs

    base_url = "https://api.github.com"

    # 根据资源类型选择 API 端点
    if ref.type in (ResourceType.ISSUE, ResourceType.PULL):
        # Issue 和 PR 都通过 /issues 端点获取
        issue_url = f"{base_url}/repos/{ref.owner}/{ref.repo}/issues/{ref.number}"
        comments_url = f"{base_url}/repos/{ref.owner}/{ref.repo}/issues/{ref.number}/comments"

        # 获取 Issue/PR 基本信息
        response = _make_request(issue_url, token)
        issue_data = response.json()

        # 检查是否是 PR
        if ref.type == ResourceType.PULL:
            pr_data = _make_request(
                f"{base_url}/repos/{ref.owner}/{ref.repo}/pulls/{ref.number}",
                token
            ).json()
        else:
            pr_data = None

        # 获取评论（分页）
        comments = _fetch_all_pages(comments_url, token)

        # 解析时间
        created_at = _parse_github_time(issue_data["created_at"])
        updated_at = _parse_github_time(issue_data["updated_at"])

        # 解析标签
        labels = [
            Label(name=label["name"], color=label.get("color"))
            for label in issue_data.get("labels", [])
        ]

        # 解析评论
        comment_objects = [
            Comment(
                author=comment["user"]["login"],
                body=comment["body"],
                created_at=_parse_github_time(comment["created_at"])
            )
            for comment in comments
        ]

        # 创建 IssueData 对象
        issue_data_obj = IssueData(
            ref=ref,
            title=issue_data["title"],
            state=issue_data["state"],
            author=issue_data["user"]["login"],
            body=issue_data["body"],
            created_at=created_at,
            updated_at=updated_at,
            labels=labels,
            comments=comment_objects,
        )

        # 如果是 PR，填充 PR 专用字段
        if ref.type == ResourceType.PULL and pr_data:
            issue_data_obj.draft = pr_data.get("draft", False)
            issue_data_obj.merged = pr_data.get("merged", False)
            issue_data_obj.mergeable = pr_data.get("mergeable")

        return issue_data_obj

    else:  # DISCUSSION
        # Discussion 使用 GraphQL API
        return _fetch_discussion(ref, token)


def _make_request(url: str, token: str | None, params: dict | None = None, data: dict | None = None, retry_on_rate_limit: bool = True) -> requests.Response:
    """发送 HTTP 请求并处理响应。

    Args:
        url: 请求 URL
        token: GitHub Token
        params: 查询参数
        data: 请求体数据（用于 POST/PUT 请求）
        retry_on_rate_limit: 是否在遇到限流时自动重试一次

    Returns:
        requests.Response

    Raises:
        GithubAPIError: API 调用失败
        RateLimitError: 触发限流且重试失败
        AuthError: Token 无效
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "issue2md/1.0.0",
    }

    if token:
        headers["Authorization"] = f"token {token}"

    try:
        # 根据是否有 data 选择请求方法
        if data is not None:
            response = requests.post(url, headers=headers, json=data)
        else:
            response = requests.get(url, headers=headers, params=params)

        # 处理响应
        _handle_response(response, token)

        # 如果触发了限流，尝试重试一次
        if retry_on_rate_limit and response.status_code == 200 and \
           response.headers.get("X-RateLimit-Remaining") == "0":
            # 已经在 _handle_response 中处理了等待
            if data is not None:
                response = requests.post(url, headers=headers, json=data)
            else:
                response = requests.get(url, headers=headers, params=params)
            _handle_response(response, token)

        return response

    except requests.exceptions.RequestException as e:
        raise GithubAPIError(f"Network error: {str(e)}") from e


def _fetch_all_pages(url: str, token: str | None) -> list:
    """获取所有分页数据。

    Args:
        url: API 端点 URL
        token: GitHub Token

    Returns:
        合并后的数据列表
    """
    from urllib.parse import parse_qs, urlparse

    all_data = []
    page = 1
    per_page = 100

    while True:
        params = {
            "page": page,
            "per_page": per_page,
        }

        response = _make_request(url, token, params)
        data = response.json()

        if not data:  # 空数据或错误
            break

        all_data.extend(data)

        # 检查是否还有更多数据
        link_header = response.headers.get("Link", "")
        if f'rel="next"' not in link_header:
            break

        page += 1

    return all_data


def _parse_github_time(time_str: str) -> datetime:
    """解析 GitHub 时间字符串为 datetime 对象。

    Args:
        time_str: GitHub 时间字符串（ISO 8601）

    Returns:
        datetime 对象（UTC）
    """
    # 使用 dateutil 解析，支持多种 ISO 8601 格式
    dt = dateutil.parser.isoparse(time_str)

    # 如果没有时区信息，假设是 UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt


def _fetch_discussion(ref: ResourceRef, token: str | None) -> "DiscussionData":
    """获取 Discussion 数据（使用 GraphQL）。

    Args:
        ref: Discussion 资源引用
        token: GitHub Token

    Returns:
        DiscussionData 对象

    Raises:
        GithubAPIError: API 调用失败
    """
    import json

    # GraphQL 查询
    query = """
    query GetDiscussion($owner: String!, $repo: String!, $number: Int!) {
        repository(owner: $owner, name: $repo) {
            discussion(number: $number) {
                title
                body
                author { login }
                createdAt
                updatedAt
                category { name }
                labels(first: 100) { nodes { name color } }
                comments(first: 100, after: $cursor) {
                    nodes {
                        author { login }
                        body
                        createdAt
                    }
                    pageInfo { hasNextPage endCursor }
                }
                answerChosen
            }
        }
    }
    """

    # GraphQL 端点
    graphql_url = "https://api.github.com/graphql"

    # 构建查询变量
    variables = {
        "owner": ref.owner,
        "repo": ref.repo,
        "number": ref.number,
        "cursor": None,
    }

    all_comments = []

    # 获取所有评论（GraphQL 分页）
    while True:
        # 执行 GraphQL 查询
        response = _make_request(
            graphql_url,
            token,
            params=None,
            data={
                "query": query,
                "variables": variables
            }
        )

        try:
            result = response.json()
        except ValueError as e:
            raise GithubAPIError(f"Invalid JSON response: {str(e)}") from e

        # 检查 GraphQL 错误
        if "errors" in result:
            error_msg = result["errors"][0].get("message", "Unknown GraphQL error")
            if "NOT_FOUND" in error_msg:
                raise GithubAPIError("Discussion not found or not enabled")
            raise GithubAPIError(f"GraphQL error: {error_msg}")

        # 提取讨论数据
        discussion = result["data"]["repository"]["discussion"]
        if not discussion:
            raise GithubAPIError("Discussion not found")

        # 处理评论
        comments_page = discussion["comments"]["nodes"]
        all_comments.extend(comments_page)

        # 检查是否还有更多评论
        page_info = discussion["comments"]["pageInfo"]
        if not page_info["hasNextPage"]:
            break

        # 准备下一页
        variables["cursor"] = page_info["endCursor"]

    # 解析标签
    labels = [
        Label(name=label["name"], color=label.get("color"))
        for label in discussion.get("labels", {}).get("nodes", [])
    ]

    # 解析评论
    comment_objects = [
        Comment(
            author=comment["author"]["login"],
            body=comment["body"],
            created_at=_parse_github_time(comment["createdAt"])
        )
        for comment in all_comments
    ]

    # 解析时间
    created_at = _parse_github_time(discussion["createdAt"])
    updated_at = _parse_github_time(discussion["updatedAt"])

    # 创建 DiscussionData 对象
    discussion_data = DiscussionData(
        ref=ref,
        title=discussion["title"],
        author=discussion["author"]["login"],
        body=discussion["body"],
        created_at=created_at,
        updated_at=updated_at,
        category=discussion["category"]["name"],
        labels=labels,
        comments=comment_objects,
        answer_chosen=discussion["answerChosen"]
    )

    return discussion_data


__all__ = ["validate_token", "fetch"]