"""GitHub Issue 集成测试"""


from typing import Any

import pytest
from requests_mock import Mocker as requests_mock

from issue2md.core.github import fetch
from issue2md.errors import GithubAPIError, RateLimitError
from issue2md.models.issue import IssueData
from issue2md.models.resource import ResourceRef, ResourceType


def test_fetch_issue_success_single_page(requests_mock: requests_mock, mocker: Any) -> None:
    """测试获取 Issue 成功（单页评论）"""
    # Mock GitHub API 响应
    issue_response = {
        "title": "Test Issue",
        "body": "This is a test issue body",
        "state": "open",
        "user": {"login": "octocat"},
        "created_at": "2023-01-02T03:04:05Z",
        "updated_at": "2023-06-01T07:08:09Z",
        "labels": [{"name": "bug", "color": "d73a4a"}, {"name": "frontend", "color": "61dafb"}],
        "pull_request": None,  # 标识为 Issue
    }

    comments_response = [
        {
            "id": 1,
            "user": {"login": "user1"},
            "body": "Comment 1",
            "created_at": "2023-01-02T04:00:00Z",
        },
        {
            "id": 2,
            "user": {"login": "user2"},
            "body": "Comment 2",
            "created_at": "2023-01-02T05:00:00Z",
        },
    ]

    # 设置 API 端点
    requests_mock.get(
        "https://api.github.com/repos/octocat/Hello-World/issues/1", json=issue_response
    )
    requests_mock.get(
        "https://api.github.com/repos/octocat/Hello-World/issues/1/comments", json=comments_response
    )

    # 执行测试
    ref = ResourceRef("octocat", "Hello-World", ResourceType.ISSUE, 1)
    data = fetch(ref, token=None)

    # 验证结果
    assert isinstance(data, IssueData)
    assert data.title == "Test Issue"
    assert data.body == "This is a test issue body"
    assert data.state == "open"
    assert data.author == "octocat"
    assert data.comments_count == 2
    assert len(data.labels) == 2
    assert data.labels[0].name == "bug"
    assert data.labels[1].name == "frontend"
    assert len(data.comments) == 2
    assert data.comments[0].author == "user1"
    assert data.comments[0].body == "Comment 1"
    assert data.comments[1].author == "user2"
    assert data.comments[1].body == "Comment 2"


def test_fetch_issue_success_multiple_pages(requests_mock: requests_mock, mocker: Any) -> None:
    """测试获取 Issue 成功（多页评论）"""
    # Mock GitHub API 响应
    issue_response: dict[str, Any] = {
        "title": "Multi-page Issue",
        "body": "Issue with many comments",
        "state": "closed",
        "user": {"login": "testuser"},
        "created_at": "2023-01-02T03:04:05Z",
        "updated_at": "2023-06-01T07:08:09Z",
        "labels": [],
        "pull_request": None,
    }

    # 第一页评论
    comments_page1 = [
        {
            "id": 1,
            "user": {"login": "user1"},
            "body": "Comment 1",
            "created_at": "2023-01-02T04:00:00Z",
        }
    ]

    # 第二页评论
    comments_page2 = [
        {
            "id": 2,
            "user": {"login": "user2"},
            "body": "Comment 2",
            "created_at": "2023-01-02T05:00:00Z",
        }
    ]

    # 设置 API 端点
    requests_mock.get(
        "https://api.github.com/repos/testuser/test-repo/issues/1", json=issue_response
    )
    requests_mock.get(
        "https://api.github.com/repos/testuser/test-repo/issues/1/comments",
        json=comments_page1,
        headers={
            "Link": '<https://api.github.com/repos/testuser/test-repo/issues/1/comments?page=2>; rel="next"'
        },
    )
    # 模分页
    requests_mock.get(
        "https://api.github.com/repos/testuser/test-repo/issues/1/comments?page=2",
        json=comments_page2,
    )

    # 执行测试
    ref = ResourceRef("testuser", "test-repo", ResourceType.ISSUE, 1)
    data = fetch(ref, token=None)

    # 验证结果
    assert isinstance(data, IssueData)
    assert data.comments_count == 2
    assert len(data.comments) == 2
    # 评论应该按时间排序
    assert data.comments[0].author == "user1"
    assert data.comments[1].author == "user2"


def test_fetch_issue_comments_sorted(requests_mock: requests_mock, mocker: Any) -> None:
    """测试评论按 created_at 升序排列"""
    # Mock GitHub API 响应（评论乱序）
    issue_response: dict[str, Any] = {
        "title": "Unsorted Comments Issue",
        "body": "Test",
        "state": "open",
        "user": {"login": "testuser"},
        "created_at": "2023-01-02T03:04:05Z",
        "updated_at": "2023-06-01T07:08:09Z",
        "labels": [],
        "pull_request": None,
    }

    # 评论创建时间乱序
    comments_response = [
        {
            "id": 2,
            "user": {"login": "user2"},
            "body": "Later comment",
            "created_at": "2023-01-02T05:00:00Z",  # 后创建
        },
        {
            "id": 1,
            "user": {"login": "user1"},
            "body": "Earlier comment",
            "created_at": "2023-01-02T04:00:00Z",  # 先创建
        },
    ]

    # 设置 API 端点
    requests_mock.get(
        "https://api.github.com/repos/testuser/test-repo/issues/1", json=issue_response
    )
    requests_mock.get(
        "https://api.github.com/repos/testuser/test-repo/issues/1/comments", json=comments_response
    )

    # 执行测试
    ref = ResourceRef("testuser", "test-repo", ResourceType.ISSUE, 1)
    data = fetch(ref, token=None)

    # 验证评论按时间升序排列
    assert data.comments[0].author == "user1"  # 早的在前
    assert data.comments[1].author == "user2"  # 晚的在后


def test_fetch_issue_network_error(requests_mock: requests_mock) -> None:
    """测试网络错误"""
    import requests

    ref = ResourceRef("nonexistent", "repo", ResourceType.ISSUE, 999)
    requests_mock.get(
        "https://api.github.com/repos/nonexistent/repo/issues/999",
        exc=requests.exceptions.ConnectionError("Connection refused"),
    )

    with pytest.raises(GithubAPIError) as exc_info:
        fetch(ref, token=None)

    assert "connect" in str(exc_info.value).lower() or "network" in str(exc_info.value).lower()


def test_fetch_issue_rate_limit_retry(requests_mock: requests_mock, mocker: Any) -> None:
    """测试限流等待时间过长时抛出 RateLimitError"""
    current_time = 1700000000
    reset_time = current_time + 700

    requests_mock.get(
        "https://api.github.com/repos/testuser/test-repo/issues/1",
        json={"message": "API rate limit exceeded"},
        status_code=200,
        headers={
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(reset_time),
        },
    )

    ref = ResourceRef("testuser", "test-repo", ResourceType.ISSUE, 1)
    mocker.patch("issue2md.core.github.time.time", return_value=current_time)

    with pytest.raises(RateLimitError):
        fetch(ref, token=None)
