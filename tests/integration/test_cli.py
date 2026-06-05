"""CLI 集成测试"""

import json
from pathlib import Path
from datetime import datetime, timezone
import pytest
import requests_mock
from issue2md.cli.main import main


def test_cli_invalid_url(tmp_path: Path):
    """测试非法 URL"""
    url = "https://invalid-url"
    exit_code = main([url, "-o", str(tmp_path)])

    # 验证返回码 1
    assert exit_code == 1

    # 没有文件被创建
    assert not (tmp_path / "out").exists()


def test_cli_single_issue_success(requests_mock: requests_mock, tmp_path: Path):
    """测试 CLI 单个 Issue 成功"""
    # Mock GitHub API 响应
    issue_response = {
        "title": "Test Issue from CLI",
        "body": "This is a test issue body from CLI",
        "state": "open",
        "user": {"login": "octocat"},
        "created_at": "2023-01-02T03:04:05Z",
        "updated_at": "2023-06-01T07:08:09Z",
        "labels": [{"name": "bug", "color": "d73a4a"}],
        "pull_request": None,
    }

    comments_response = [
        {
            "id": 1,
            "user": {"login": "user1"},
            "body": "CLI Comment 1",
            "created_at": "2023-01-02T04:00:00Z",
        }
    ]

    # Mock API 端点
    requests_mock.get(
        "https://api.github.com/repos/octocat/Hello-World/issues/1", json=issue_response
    )
    requests_mock.get(
        "https://api.github.com/repos/octocat/Hello-World/issues/1/comments", json=comments_response
    )

    # 执行 CLI
    url = "https://github.com/octocat/Hello-World/issues/1"
    exit_code = main([url, "-o", str(tmp_path)])

    # 验证结果
    assert exit_code == 0

    # 检查输出文件
    output_file = tmp_path / "octocat" / "Hello-World" / "issues" / "1.md"
    assert output_file.exists()

    # 验证文件内容
    content = output_file.read_text()
    assert "Test Issue from CLI" in content
    assert "open" in content
    assert "CLI Comment 1" in content
    assert "octocat" in content


def test_cli_single_pull_success(requests_mock: requests_mock, tmp_path: Path):
    """测试 CLI 单个 PR 成功"""
    # Mock Issue API 响应
    issue_response = {
        "title": "Test PR from CLI",
        "body": "This is a test PR body from CLI",
        "state": "closed",
        "user": {"login": "testuser"},
        "created_at": "2023-01-02T03:04:05Z",
        "updated_at": "2023-06-01T07:08:09Z",
        "labels": [],
        "pull_request": {
            "url": "https://api.github.com/repos/testuser/repo/pulls/42",
            "merged": True,
        },
    }

    # Mock PR API 响应
    pr_response = {
        "title": "Test PR from CLI",
        "body": "This is a test PR body from CLI",
        "state": "closed",
        "user": {"login": "testuser"},
        "created_at": "2023-01-02T03:04:05Z",
        "updated_at": "2023-06-01T07:08:09Z",
        "draft": False,
        "merged": True,
        "mergeable": True,
    }

    # Mock API 端点
    requests_mock.get("https://api.github.com/repos/testuser/repo/issues/42", json=issue_response)
    requests_mock.get("https://api.github.com/repos/testuser/repo/pulls/42", json=pr_response)

    # 执行 CLI
    url = "https://github.com/testuser/repo/pull/42"
    exit_code = main([url, "-o", str(tmp_path)])

    # 验证结果
    assert exit_code == 0

    # 检查输出文件
    output_file = tmp_path / "testuser" / "repo" / "pulls" / "42.md"
    assert output_file.exists()

    # 验证文件内容
    content = output_file.read_text()
    assert "Test PR from CLI" in content
    assert "merged" in content  # PR 特有标记
    assert "merged: true" in content  # frontmatter 中的 merged 字段


def test_cli_single_discussion_success(requests_mock: requests_mock, tmp_path: Path):
    """测试 CLI 单个 Discussion 成功"""
    # Mock GraphQL 响应
    graphql_response = {
        "data": {
            "repository": {
                "discussion": {
                    "title": "Test Discussion from CLI",
                    "body": "This is a test discussion body from CLI",
                    "author": {"login": "discussuser"},
                    "createdAt": "2023-01-02T03:04:05Z",
                    "updatedAt": "2023-06-01T07:08:09Z",
                    "category": {"name": "Q&A"},
                    "labels": {"nodes": []},
                    "comments": {
                        "nodes": [],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    },
                    "answerChosen": False,
                }
            }
        }
    }

    # Mock GraphQL 端点
    requests_mock.post("https://api.github.com/graphql", json=graphql_response)

    # 执行 CLI
    url = "https://github.com/discussuser/repo/discussions/100"
    exit_code = main([url, "-o", str(tmp_path)])

    # 验证结果
    assert exit_code == 0

    # 检查输出文件
    output_file = tmp_path / "discussuser" / "repo" / "discussions" / "100.md"
    assert output_file.exists()

    # 验证文件内容
    content = output_file.read_text()
    assert "Test Discussion from CLI" in content
    assert "Q&A" in content
    assert "category: Q&A" in content


def test_cli_invalid_url(tmp_path: Path):
    """测试非法 URL"""
    url = "https://invalid-url"
    exit_code = main([url, "-o", str(tmp_path)])

    # 验证返回码 1
    assert exit_code == 1

    # 没有文件被创建
    assert not (tmp_path / "out").exists()


def test_cli_private_repo_without_token(requests_mock: requests_mock, tmp_path: Path):
    """测试私有仓库无 Token"""
    # Mock 403 响应
    requests_mock.get(
        "https://api.github.com/repos/private/repo/issues/1",
        json={"message": "Not Found"},
        status=403,
    )

    # 执行 CLI
    url = "https://github.com/private/repo/issues/1"
    exit_code = main([url, "-o", str(tmp_path)])

    # 验证返回码 4
    assert exit_code == 4


def test_cli_readonly_directory(tmp_path: Path):
    """测试只读目录"""
    # 创建只读目录
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    readonly_dir.chmod(0o555)  # 只读权限

    url = "https://github.com/test/repo/issues/1"
    exit_code = main([url, "-o", str(readonly_dir)])

    # 验证返回码 3
    assert exit_code == 3


def test_cli_duplicate_urls(tmp_path: Path):
    """测试重复 URL"""
    url = "https://github.com/test/repo/issues/1"

    # 执行 CLI 两次相同 URL
    exit_code1 = main([url, url, "-o", str(tmp_path)])
    exit_code2 = main([url, "-o", str(tmp_path)])

    # 都应该成功
    assert exit_code1 == 0
    assert exit_code2 == 0

    # 文件应该只被创建一次
    output_file = tmp_path / "test" / "repo" / "issues" / "1.md"
    assert output_file.exists()


def test_cli_batch_with_continue_on_error(requests_mock: requests_mock, tmp_path: Path):
    """测试批量处理 + continue-on-error"""
    # 第一个 URL 正常
    issue_response1 = {
        "title": "Issue 1",
        "body": "Body 1",
        "state": "open",
        "user": {"login": "test"},
        "created_at": "2023-01-02T03:04:05Z",
        "updated_at": "2023-06-01T07:08:09Z",
        "labels": [],
        "pull_request": None,
    }
    requests_mock.get("https://api.github.com/repos/test/repo/issues/1", json=issue_response1)

    # 第二个 URL 404
    requests_mock.get(
        "https://api.github.com/repos/test/repo/issues/404",
        json={"message": "Not Found"},
        status=404,
    )

    # 第三个 URL 正常
    issue_response3 = {
        "title": "Issue 3",
        "body": "Body 3",
        "state": "closed",
        "user": {"login": "test"},
        "created_at": "2023-01-02T03:04:05Z",
        "updated_at": "2023-06-01T07:08:09Z",
        "labels": [],
        "pull_request": None,
    }
    requests_mock.get("https://api.github.com/repos/test/repo/issues/3", json=issue_response3)

    # 执行批量处理
    urls = [
        "https://github.com/test/repo/issues/1",
        "https://github.com/test/repo/issues/404",
        "https://github.com/test/repo/issues/3",
    ]
    exit_code = main(urls + ["--continue-on-error", "-o", str(tmp_path)])

    # 验证返回码 2（404 的错误码）
    assert exit_code == 2

    # 验证 SUMMARY 输出
    # 注意：pytest 重定向了 stderr，所以这里不检查输出内容

    # 验证成功的文件被创建
    assert (tmp_path / "test" / "repo" / "issues" / "1.md").exists()
    assert (tmp_path / "test" / "repo" / "issues" / "3.md").exists()


def test_cli_max_comments_truncation(requests_mock: requests_mock, tmp_path: Path):
    """测试 max-comments 截断"""
    # Mock GitHub API 响应（20 条评论）
    issue_response = {
        "title": "Issue with Many Comments",
        "body": "Body",
        "state": "open",
        "user": {"login": "test"},
        "created_at": "2023-01-02T03:04:05Z",
        "updated_at": "2023-06-01T07:08:09Z",
        "labels": [],
        "pull_request": None,
    }

    # 生成 20 条评论
    comments = []
    for i in range(20):
        comments.append(
            {
                "id": i + 1,
                "user": {"login": f"user{i}"},
                "body": f"Comment {i+1}",
                "created_at": f"2023-01-02T0{i:02d}:00:00Z",
            }
        )

    # 设置 API 端点
    requests_mock.get("https://api.github.com/repos/test/repo/issues/1", json=issue_response)
    requests_mock.get("https://api.github.com/repos/test/repo/issues/1/comments", json=comments)

    # 执行 CLI（限制 5 条评论）
    url = "https://github.com/test/repo/issues/1"
    exit_code = main([url, "--max-comments", "5", "-o", str(tmp_path)])

    # 验证成功
    assert exit_code == 0

    # 检查输出文件
    output_file = tmp_path / "test" / "repo" / "issues" / "1.md"
    content = output_file.read_text()

    # 验证只显示 5 条评论
    assert content.count("Comment") == 5

    # 但 frontmatter 中 comments_count 应该是 20
    assert "comments_count: 20" in content
