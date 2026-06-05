"""验收测试 - 覆盖所有 AC 场景"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from requests_mock import Mocker as requests_mock

from issue2md.cli.main import main


def _issue_json(title: str, body: str = "Body", state: str = "open") -> dict[str, Any]:
    """构造 Issue API 响应 JSON"""
    return {
        "title": title,
        "state": state,
        "user": {"login": "octocat"},
        "body": body,
        "created_at": "2026-01-02T03:04:05Z",
        "updated_at": "2026-06-01T07:08:09Z",
        "labels": [],
        "pull_request": None,
    }


def _discussion_graphql_response(
    comments: list[dict],
    *,
    has_next_page: bool = False,
    end_cursor: str | None = None,
) -> dict[str, Any]:
    """构造 Discussion GraphQL 响应 JSON"""
    return {
        "data": {
            "repository": {
                "discussion": {
                    "title": "Long Discussion",
                    "body": "A discussion with many comments",
                    "author": {"login": "octocat"},
                    "createdAt": "2026-01-02T03:04:05Z",
                    "updatedAt": "2026-06-01T07:08:09Z",
                    "category": {"name": "Q&A"},
                    "labels": {"nodes": []},
                    "comments": {
                        "nodes": comments,
                        "pageInfo": {
                            "hasNextPage": has_next_page,
                            "endCursor": end_cursor,
                        },
                    },
                    "answerChosen": False,
                }
            }
        }
    }


class TestAcceptance:
    """验收测试类，覆盖所有 AC 场景"""

    def setup_method(self) -> None:
        """每个测试前执行"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def teardown_method(self) -> None:
        """每个测试后执行"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_ac1_single_issue_success(self, requests_mock: requests_mock) -> None:
        """AC1: 单个 Issue 成功场景"""
        # Mock GitHub API 响应
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/1",
            json={
                "title": "Test Issue",
                "state": "open",
                "user": {"login": "octocat"},
                "body": "Test body content",
                "created_at": "2026-01-02T03:04:05Z",
                "updated_at": "2026-06-01T07:08:09Z",
                "labels": [{"name": "bug", "color": "d73a4a"}],
                "pull_request": None,
            },
        )
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/1/comments",
            json=[
                {
                    "user": {"login": "user1"},
                    "body": "Comment 1 content",
                    "created_at": "2026-01-03T04:05:06Z",
                },
                {
                    "user": {"login": "user2"},
                    "body": "Comment 2 content",
                    "created_at": "2026-01-04T05:06:07Z",
                },
            ],
        )

        # 执行测试
        url = "https://github.com/octocat/Hello-World/issues/1"
        exit_code = main([url])

        # 验证结果
        assert exit_code == 0
        output_file = Path(self.temp_dir) / "out" / "octocat" / "Hello-World" / "issues" / "1.md"
        assert output_file.exists()
        content = output_file.read_text()
        assert "Test Issue" in content
        assert "Comment 1 content" in content
        assert "Comment 2 content" in content

    def test_ac2_rate_limit_retry(self, requests_mock: requests_mock, mocker) -> None:
        """AC2: 限流重试场景 — 验证等待后自动重试并成功"""
        current_time = 1_700_000_000
        reset_time = current_time + 5
        issue_url = "https://api.github.com/repos/octocat/Hello-World/issues/1"
        comments_url = "https://api.github.com/repos/octocat/Hello-World/issues/1/comments"

        # 第一次 200 + 限流头触发等待；第二次返回正常数据
        requests_mock.get(
            issue_url,
            [
                {
                    "json": {},
                    "status_code": 200,
                    "headers": {
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_time),
                    },
                },
                {
                    "json": _issue_json("Test Issue", "Test body"),
                    "status_code": 200,
                    "headers": {"X-RateLimit-Remaining": "100"},
                },
            ],
        )
        requests_mock.get(comments_url, json=[])

        mock_sleep = mocker.patch("issue2md.core.github.time.sleep")
        mocker.patch("issue2md.core.github.time.time", return_value=current_time)

        exit_code = main(["https://github.com/octocat/Hello-World/issues/1"])

        assert exit_code == 0
        mock_sleep.assert_called_once_with(5)
        output_file = Path(self.temp_dir) / "out" / "octocat" / "Hello-World" / "issues" / "1.md"
        assert output_file.exists()
        assert "Test Issue" in output_file.read_text()

    def test_ac3_single_pull_success(self, requests_mock: requests_mock) -> None:
        """AC3: 单个 PR 成功场景"""
        # Mock PR 响应
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/1",
            json={
                "title": "Test PR",
                "state": "open",
                "user": {"login": "octocat"},
                "body": "PR body content",
                "created_at": "2026-01-02T03:04:05Z",
                "updated_at": "2026-06-01T07:08:09Z",
                "labels": [],
                "pull_request": {"html_url": "https://github.com/octocat/Hello-World/pull/1"},
            },
        )
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/pulls/1",
            json={
                "draft": False,
                "merged": False,
                "mergeable": True,
            },
        )
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/1/comments",
            json=[],
        )
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/pulls/1/comments",
            json=[],
        )

        # 执行测试
        url = "https://github.com/octocat/Hello-World/pull/1"
        exit_code = main([url])

        # 验证结果
        assert exit_code == 0
        output_file = Path(self.temp_dir) / "out" / "octocat" / "Hello-World" / "pulls" / "1.md"
        assert output_file.exists()
        content = output_file.read_text()
        assert "Test PR" in content
        assert "draft: false" in content
        assert "merged: false" in content
        assert "mergeable: true" in content

    def test_ac4_discussion_success(self, requests_mock: requests_mock) -> None:
        """AC4: Discussion 成功场景"""
        # Mock GraphQL 响应
        requests_mock.post(
            "https://api.github.com/graphql",
            json={
                "data": {
                    "repository": {
                        "discussion": {
                            "title": "Test Discussion",
                            "body": "Discussion body content",
                            "author": {"login": "octocat"},
                            "createdAt": "2026-01-02T03:04:05Z",
                            "updatedAt": "2026-06-01T07:08:09Z",
                            "category": {"name": "General"},
                            "labels": {"nodes": [{"name": "bug", "color": "d73a4a"}]},
                            "answerChosen": False,
                            "comments": {"nodes": [], "pageInfo": {"hasNextPage": False}},
                        }
                    }
                }
            }
        )

        # 执行测试
        url = "https://github.com/octocat/Hello-World/discussions/1"
        exit_code = main([url])

        # 验证结果
        assert exit_code == 0
        output_file = (
            Path(self.temp_dir) / "out" / "octocat" / "Hello-World" / "discussions" / "1.md"
        )
        assert output_file.exists()
        content = output_file.read_text()
        assert "Test Discussion" in content
        assert "category: General" in content  # 检查 Discussion 专用字段

    def test_ac5_batch_continue_on_error(self, requests_mock: requests_mock, capsys) -> None:
        """AC5: 批量 + continue-on-error 完整流程"""
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/1",
            json=_issue_json("Test Issue 1", "Body 1"),
        )
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/1/comments",
            json=[],
        )

        # 第二个 URL 404
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/2",
            json={"message": "Not Found"},
            status_code=404,
        )

        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/3",
            json=_issue_json("Test Issue 3", "Body 3"),
        )
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/3/comments",
            json=[],
        )

        urls = [
            "https://github.com/octocat/Hello-World/issues/1",
            "https://github.com/octocat/Hello-World/issues/2",
            "https://github.com/octocat/Hello-World/issues/3",
        ]
        exit_code = main(urls + ["--continue-on-error"])

        assert exit_code == 2
        output_dir = Path(self.temp_dir) / "out" / "octocat" / "Hello-World" / "issues"
        assert (output_dir / "1.md").exists()
        assert not (output_dir / "2.md").exists()
        assert (output_dir / "3.md").exists()

        captured = capsys.readouterr()
        assert "[SUMMARY] processed=3, succeeded=2, failed=1" in captured.err
        assert "issues/2" in captured.err

    def test_ac6_invalid_url(self) -> None:
        """AC6: 非法 URL 场景"""
        # 执行测试
        exit_code = main(["https://invalid-url"])

        # 验证结果
        assert exit_code == 1

    def test_ac7_auth_failure(self, requests_mock: requests_mock) -> None:
        """AC7: 鉴权失败场景"""
        requests_mock.get(
            "https://api.github.com/repos/private/repo/issues/1",
            json={"message": "Forbidden"},
            status_code=403,
            headers={"X-RateLimit-Remaining": "100"},
        )

        # 执行测试
        exit_code = main(["https://github.com/private/repo/issues/1"])

        # 验证结果
        assert exit_code == 4

    def test_ac8_io_error(self, requests_mock: requests_mock) -> None:
        """AC8: IO 错误场景（只读目录）"""
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/1",
            json=_issue_json("Test Issue"),
        )
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/1/comments",
            json=[],
        )

        output_dir = Path(self.temp_dir) / "out"
        output_dir.mkdir(parents=True)
        output_dir.chmod(0o555)  # 设置为只读

        # 执行测试
        exit_code = main(["https://github.com/octocat/Hello-World/issues/1", "-o", str(output_dir)])

        # 验证结果
        assert exit_code == 3

    def test_ac9_url_deduplication(self, requests_mock: requests_mock) -> None:
        """AC9: URL 去重场景"""
        # Mock 响应
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/1",
            json={
                "title": "Test Issue",
                "state": "open",
                "user": {"login": "octocat"},
                "body": "Body",
                "created_at": "2026-01-02T03:04:05Z",
                "updated_at": "2026-06-01T07:08:09Z",
                "labels": [],
                "pull_request": None,
            },
        )
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/1/comments",
            json=[],
        )

        # 执行测试 - 重复 URL
        urls = [
            "https://github.com/octocat/Hello-World/issues/1",
            "https://github.com/octocat/Hello-World/issues/1",  # 重复
        ]
        exit_code = main(urls)

        # 验证结果
        assert exit_code == 0
        output_file = Path(self.temp_dir) / "out" / "octocat" / "Hello-World" / "issues" / "1.md"
        assert output_file.exists()
        # 只应该有一个文件

    def test_ac10_max_comments_truncation(self, requests_mock: requests_mock) -> None:
        """AC10: max-comments 截断场景"""
        # Mock 响应 - 5 条评论
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/1",
            json={
                "title": "Test Issue",
                "state": "open",
                "user": {"login": "octocat"},
                "body": "Body",
                "created_at": "2026-01-02T03:04:05Z",
                "updated_at": "2026-06-01T07:08:09Z",
                "labels": [],
                "pull_request": None,
            },
        )
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/1/comments",
            json=[
                {
                    "user": {"login": "user1"},
                    "body": "Comment 1",
                    "created_at": "2026-01-03T04:05:06Z",
                },
                {
                    "user": {"login": "user2"},
                    "body": "Comment 2",
                    "created_at": "2026-01-04T05:06:07Z",
                },
                {
                    "user": {"login": "user3"},
                    "body": "Comment 3",
                    "created_at": "2026-01-05T06:07:08Z",
                },
                {
                    "user": {"login": "user4"},
                    "body": "Comment 4",
                    "created_at": "2026-01-06T07:08:09Z",
                },
                {
                    "user": {"login": "user5"},
                    "body": "Comment 5",
                    "created_at": "2026-01-07T08:09:10Z",
                },
            ],
        )

        # 执行测试 - 限制为 3 条评论
        exit_code = main(["https://github.com/octocat/Hello-World/issues/1", "--max-comments=3"])

        # 验证结果
        assert exit_code == 0
        output_file = Path(self.temp_dir) / "out" / "octocat" / "Hello-World" / "issues" / "1.md"
        content = output_file.read_text()
        assert "Comment 1" in content
        assert "Comment 2" in content
        assert "Comment 3" in content
        assert "Comment 4" not in content  # 应该被截断
        assert "Comment 5" not in content  # 应该被截断

    def test_output_structure(self, requests_mock: requests_mock) -> None:
        """验证输出目录结构"""
        # Mock 响应
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/1",
            json={
                "title": "Test Issue",
                "state": "open",
                "user": {"login": "octocat"},
                "body": "Body",
                "created_at": "2026-01-02T03:04:05Z",
                "updated_at": "2026-06-01T07:08:09Z",
                "labels": [],
                "pull_request": None,
            },
        )
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/1/comments",
            json=[],
        )

        # 执行测试
        exit_code = main(["https://github.com/octocat/Hello-World/issues/1"])

        # 验证目录结构
        assert exit_code == 0
        output_dir = Path(self.temp_dir) / "out"
        assert output_dir.exists()
        assert (output_dir / "octocat" / "Hello-World" / "issues" / "1.md").exists()

    def test_frontmatter_format(self, requests_mock: requests_mock) -> None:
        """验证 frontmatter 格式"""
        # Mock 响应
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/1",
            json={
                "title": "Test Issue",
                "state": "open",
                "user": {"login": "octocat"},
                "body": "Body",
                "created_at": "2026-01-02T03:04:05Z",
                "updated_at": "2026-06-01T07:08:09Z",
                "labels": [{"name": "bug", "color": "d73a4a"}],
                "pull_request": None,
            },
        )
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/1/comments",
            json=[],
        )

        # 执行测试
        exit_code = main(["https://github.com/octocat/Hello-World/issues/1"])

        # 验证 frontmatter
        assert exit_code == 0
        output_file = Path(self.temp_dir) / "out" / "octocat" / "Hello-World" / "issues" / "1.md"
        content = output_file.read_text()

        # 检查 YAML frontmatter
        assert content.startswith("---")
        assert "url: https://github.com/octocat/Hello-World/issues/1" in content
        assert "type: issue" in content
        assert "owner: octocat" in content
        assert "repo: Hello-World" in content
        assert "number: 1" in content
        assert "title: Test Issue" in content
        assert "state: open" in content
        assert "author: octocat" in content
        assert "2026-01-02T03:04:05" in content
        assert "2026-06-01T07:08:09" in content
        assert "labels:" in content
        assert "- bug" in content
        assert "comments_count: 0" in content
        assert "fetched_at:" in content  # 应该有当前时间

    def test_comments_ordering(self, requests_mock: requests_mock) -> None:
        """验证评论按时间排序"""
        # Mock 响应 - 评论按时间倒序（创建时间晚的在前）
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/1",
            json={
                "title": "Test Issue",
                "state": "open",
                "user": {"login": "octocat"},
                "body": "Body",
                "created_at": "2026-01-02T03:04:05Z",
                "updated_at": "2026-06-01T07:08:09Z",
                "labels": [],
                "pull_request": None,
            },
        )
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/1/comments",
            json=[
                {
                    "user": {"login": "user2"},
                    "body": "Comment 2 (later)",
                    "created_at": "2026-01-04T05:06:07Z",
                },
                {
                    "user": {"login": "user1"},
                    "body": "Comment 1 (earlier)",
                    "created_at": "2026-01-03T04:05:06Z",
                },
            ],
        )

        # 执行测试
        exit_code = main(["https://github.com/octocat/Hello-World/issues/1"])

        # 验证结果 - 评论应该按 created_at 升序排列
        assert exit_code == 0
        output_file = Path(self.temp_dir) / "out" / "octocat" / "Hello-World" / "issues" / "1.md"
        content = output_file.read_text()

        # 检查评论顺序
        assert "Comment 1 — @user1" in content  # 应该先出现
        assert "Comment 2 — @user2" in content  # 应该后出现

    def test_ac11_discussion_recursive_paging(self, requests_mock: requests_mock) -> None:
        """AC11: Discussion GraphQL 多页评论分页"""
        first_page = _discussion_graphql_response(
            [
                {
                    "author": {"login": "user1"},
                    "body": "Comment 1",
                    "createdAt": "2026-01-03T04:05:06Z",
                },
                {
                    "author": {"login": "user2"},
                    "body": "Comment 2",
                    "createdAt": "2026-01-04T05:06:07Z",
                },
            ],
            has_next_page=True,
            end_cursor="cursor1",
        )
        second_page = _discussion_graphql_response(
            [
                {
                    "author": {"login": "user3"},
                    "body": "Comment 3",
                    "createdAt": "2026-01-05T06:07:08Z",
                },
                {
                    "author": {"login": "user4"},
                    "body": "Comment 4",
                    "createdAt": "2026-01-06T07:08:09Z",
                },
            ],
        )

        requests_mock.post(
            "https://api.github.com/graphql",
            [{"json": first_page}, {"json": second_page}],
        )

        exit_code = main(["https://github.com/octocat/Hello-World/discussions/1"])

        assert exit_code == 0
        output_file = (
            Path(self.temp_dir) / "out" / "octocat" / "Hello-World" / "discussions" / "1.md"
        )
        content = output_file.read_text()
        assert "comments_count: 4" in content
        assert "Comment 1" in content
        assert "Comment 2" in content
        assert "Comment 3" in content
        assert "Comment 4" in content

    def test_ac12_pr_draft_merged_mergeable_fields(self, requests_mock: requests_mock, mocker: Any) -> None:
        """AC12: PR draft/merged/mergeable 字段完整验证"""
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/42",
            json={
                "title": "Draft PR",
                "state": "open",
                "user": {"login": "octocat"},
                "body": "PR body",
                "created_at": "2026-01-02T03:04:05Z",
                "updated_at": "2026-06-01T07:08:09Z",
                "labels": [],
                "pull_request": {"html_url": "https://github.com/octocat/Hello-World/pull/42"},
            },
        )
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/pulls/42",
            json={
                "draft": True,
                "merged": True,
                "mergeable": None,
            },
        )
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/issues/42/comments",
            json=[],
        )
        requests_mock.get(
            "https://api.github.com/repos/octocat/Hello-World/pulls/42/comments",
            json=[],
        )

        exit_code = main(["https://github.com/octocat/Hello-World/pull/42"])

        assert exit_code == 0
        output_file = Path(self.temp_dir) / "out" / "octocat" / "Hello-World" / "pulls" / "42.md"
        content = output_file.read_text()
        assert "draft: true" in content
        assert "merged: true" in content
        assert "mergeable:" not in content
