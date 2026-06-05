"""GitHub Pull Request 集成测试"""

# import json  # 未使用，已移除
# from datetime import datetime, timezone  # 未使用，已移除
# from pathlib import Path  # 未使用，已移除
# import pytest  # 未使用，已移除

from requests_mock import Mocker as requests_mock

from issue2md.core.github import fetch
from issue2md.models.issue import IssueData
from issue2md.models.resource import ResourceRef, ResourceType


def test_fetch_pr_success(requests_mock: requests_mock) -> None:
    """测试获取 PR 成功"""
    # Mock Issue/PR API 响应
    issue_response = {
        "title": "Test PR",
        "body": "This is a test PR body",
        "state": "open",
        "user": {"login": "octocat"},
        "created_at": "2023-01-02T03:04:05Z",
        "updated_at": "2023-06-01T07:08:09Z",
        "labels": [{"name": "enhancement", "color": "84b6eb"}],
        "pull_request": {
            "url": "https://api.github.com/repos/octocat/Hello-World/pulls/1",
            "html_url": "https://github.com/octocat/Hello-World/pull/1",
            "diff_url": "https://github.com/octocat/Hello-World/pull/1.diff",
            "patch_url": "https://github.com/octocat/Hello-World/pull/1.patch",
            "merged": False,
            "mergeable": True,
            "draft": False,
        },
    }

    # Mock PR API 响应
    pr_response = {
        "title": "Test PR",
        "body": "This is a test PR body",
        "state": "merged",
        "user": {"login": "octocat"},
        "created_at": "2023-01-02T03:04:05Z",
        "updated_at": "2023-06-01T07:08:09Z",
        "draft": False,
        "merged": True,
        "mergeable": True,
        "merged_at": "2023-01-02T04:00:00Z",
    }

    # Mock 评论响应
    comments_response = [
        {
            "id": 1,
            "user": {"login": "user1"},
            "body": "PR Comment 1",
            "created_at": "2023-01-02T04:00:00Z",
        },
        {
            "id": 2,
            "user": {"login": "user2"},
            "body": "PR Comment 2",
            "created_at": "2023-01-02T05:00:00Z",
        },
    ]

    # 设置 API 端点
    requests_mock.get(
        "https://api.github.com/repos/octocat/Hello-World/issues/1", json=issue_response
    )
    requests_mock.get("https://api.github.com/repos/octocat/Hello-World/pulls/1", json=pr_response)
    requests_mock.get(
        "https://api.github.com/repos/octocat/Hello-World/issues/1/comments", json=comments_response
    )
    requests_mock.get(
        "https://api.github.com/repos/octocat/Hello-World/pulls/1/comments", json=[]
    )

    # 执行测试
    ref = ResourceRef("octocat", "Hello-World", ResourceType.PULL, 1)
    data = fetch(ref, token=None)

    # 验证结果
    assert isinstance(data, IssueData)
    assert data.title == "Test PR"
    assert data.state == "open"
    assert data.author == "octocat"
    assert data.comments_count == 2
    assert len(data.labels) == 1
    assert data.labels[0].name == "enhancement"

    # 验证 PR 专用字段
    assert data.draft is False
    assert data.merged is True
    assert data.mergeable is True


def test_fetch_pr_field_completeness(requests_mock: requests_mock) -> None:
    """测试 PR 字段完整性"""
    # Mock Issue API 响应
    issue_response = {
        "title": "Draft PR",
        "body": "Draft PR body",
        "state": "open",
        "user": {"login": "testuser"},
        "created_at": "2023-01-02T03:04:05Z",
        "updated_at": "2023-06-01T07:08:09Z",
        "labels": [],
        "pull_request": {
            "url": "https://api.github.com/repos/testuser/repo/pulls/42",
            "merged": False,
            "mergeable": None,
            "draft": True,
        },
    }

    # Mock PR API 响应
    pr_response = {
        "title": "Draft PR",
        "body": "Draft PR body",
        "state": "open",
        "user": {"login": "testuser"},
        "created_at": "2023-01-02T03:04:05Z",
        "updated_at": "2023-06-01T07:08:09Z",
        "draft": True,
        "merged": False,
        "mergeable": None,
    }

    # 设置 API 端点
    requests_mock.get("https://api.github.com/repos/testuser/repo/issues/42", json=issue_response)
    requests_mock.get("https://api.github.com/repos/testuser/repo/pulls/42", json=pr_response)
    requests_mock.get("https://api.github.com/repos/testuser/repo/issues/42/comments", json=[])
    requests_mock.get("https://api.github.com/repos/testuser/repo/pulls/42/comments", json=[])

    # 执行测试
    ref = ResourceRef("testuser", "repo", ResourceType.PULL, 42)
    data = fetch(ref, token=None)

    # 验证 PR 专用字段（明确类型为 IssueData）
    assert isinstance(data, IssueData)
    assert data.draft is True
    assert data.merged is False
    assert data.mergeable is None


def test_fetch_pr_merged_state(requests_mock: requests_mock) -> None:
    """测试 PR state 为 merged"""
    # Mock Issue API 响应
    issue_response = {
        "title": "Merged PR",
        "body": "This PR was merged",
        "state": "closed",
        "user": {"login": "testuser"},
        "created_at": "2023-01-02T03:04:05Z",
        "updated_at": "2023-06-01T07:08:09Z",
        "labels": [],
        "pull_request": {
            "url": "https://api.github.com/repos/testuser/repo/pulls/123",
            "merged": True,
        },
    }

    # Mock PR API 响应
    pr_response = {
        "title": "Merged PR",
        "body": "This PR was merged",
        "state": "closed",
        "user": {"login": "testuser"},
        "created_at": "2023-01-02T03:04:05Z",
        "updated_at": "2023-06-01T07:08:09Z",
        "draft": False,
        "merged": True,
        "mergeable": True,
        "merged_at": "2023-01-02T04:00:00Z",
    }

    # 设置 API 端点
    requests_mock.get("https://api.github.com/repos/testuser/repo/issues/123", json=issue_response)
    requests_mock.get("https://api.github.com/repos/testuser/repo/pulls/123", json=pr_response)
    requests_mock.get("https://api.github.com/repos/testuser/repo/issues/123/comments", json=[])
    requests_mock.get("https://api.github.com/repos/testuser/repo/pulls/123/comments", json=[])

    # 执行测试
    ref = ResourceRef("testuser", "repo", ResourceType.PULL, 123)
    data = fetch(ref, token=None)

    # 验证 state 为 merged（这是 IssueData 的扩展）
    assert isinstance(data, IssueData)
    assert data.state == "closed"  # Issue 状态保持 closed
    assert data.merged is True  # PR 特有字段为 True
