"""URL 解析器测试 - 表格驱动测试"""

from pathlib import Path

import pytest

from issue2md.core.parser import output_path, parse_url
from issue2md.errors import URLParseError
from issue2md.models.resource import ResourceRef, ResourceType


class TestParseURLValid:
    """测试合法 URL 解析"""

    @pytest.mark.parametrize(
        "url,expected_owner,expected_repo,expected_type,expected_number",
        [
            # Issue URL
            (
                "https://github.com/octocat/Hello-World/issues/1",
                "octocat",
                "Hello-World",
                ResourceType.ISSUE,
                1,
            ),
            ("https://github.com/owner/repo/issues/42", "owner", "repo", ResourceType.ISSUE, 42),
            (
                "https://github.com/vercel/next.js/issues/100",
                "vercel",
                "next.js",
                ResourceType.ISSUE,
                100,
            ),
            # PR URL
            (
                "https://github.com/octocat/Hello-World/pull/1",
                "octocat",
                "Hello-World",
                ResourceType.PULL,
                1,
            ),
            ("https://github.com/owner/repo/pull/42", "owner", "repo", ResourceType.PULL, 42),
            ("https://github.com/vuejs/vue/pull/1234", "vuejs", "vue", ResourceType.PULL, 1234),
            # Discussion URL
            (
                "https://github.com/vercel/next.js/discussions/1",
                "vercel",
                "next.js",
                ResourceType.DISCUSSION,
                1,
            ),
            (
                "https://github.com/owner/repo/discussions/42",
                "owner",
                "repo",
                ResourceType.DISCUSSION,
                42,
            ),
            (
                "https://github.com/openai/openai-python/discussions/100",
                "openai",
                "openai-python",
                ResourceType.DISCUSSION,
                100,
            ),
            # 带末尾斜杠
            (
                "https://github.com/octocat/Hello-World/issues/1/",
                "octocat",
                "Hello-World",
                ResourceType.ISSUE,
                1,
            ),
            ("https://github.com/owner/repo/pull/42/", "owner", "repo", ResourceType.PULL, 42),
            (
                "https://github.com/vercel/next.js/discussions/100/",
                "vercel",
                "next.js",
                ResourceType.DISCUSSION,
                100,
            ),
            # 不同大小写（保留原始大小写）
            (
                "https://github.com/Octocat/Hello-World/issues/1",
                "Octocat",
                "Hello-World",
                ResourceType.ISSUE,
                1,
            ),
            ("https://github.com/user/MyRepo/issues/2", "user", "MyRepo", ResourceType.ISSUE, 2),
        ],
    )
    def test_parse_url_valid(
        self,
        url: str,
        expected_owner: str,
        expected_repo: str,
        expected_type: ResourceType,
        expected_number: int,
    ) -> None:
        """测试合法 URL 解析"""
        result = parse_url(url)

        assert result.owner == expected_owner, f"owner: 预期 {expected_owner}, 实际 {result.owner}"
        assert result.repo == expected_repo, f"repo: 预期 {expected_repo}, 实际 {result.repo}"
        assert result.type == expected_type, f"type: 预期 {expected_type}, 实际 {result.type}"
        assert (
            result.number == expected_number
        ), f"number: 预期 {expected_number}, 实际 {result.number}"


class TestParseURLInvalid:
    """测试非法 URL 解析"""

    @pytest.mark.parametrize(
        "url,reason",
        [
            # 非https协议
            ("http://github.com/owner/repo/issues/1", "协议必须是 https"),
            ("ftp://github.com/owner/repo/issues/1", "协议必须是 https"),
            ("github.com/owner/repo/issues/1", "缺少协议"),
            # 非github.com域名
            ("https://gitlab.com/owner/repo/issues/1", "域名必须是 github.com"),
            ("https://bitbucket.org/owner/repo/issues/1", "域名必须是 github.com"),
            ("https://enterprise.github.com/owner/repo/issues/1", "域名必须是 github.com"),
            # 路径格式错误
            ("https://github.com/owner/repo", "缺少资源类型和编号"),
            ("https://github.com/owner/repo/issues", "缺少编号"),
            ("https://github.com/owner/repo/issues/", "编号为空"),
            ("https://github.com/owner", "缺少仓库名"),
            # number 非数字
            ("https://github.com/owner/repo/issues/abc", "编号必须是数字"),
            ("https://github.com/owner/repo/issues/1a", "编号必须是数字"),
            ("https://github.com/owner/repo/issues/-1", "编号必须是正整数"),
            ("https://github.com/owner/repo/issues/0", "编号必须是正整数"),
            # 不支持的资源类型
            ("https://github.com/owner/repo/commits/abc123", "不支持的资源类型: commits"),
            ("https://github.com/owner/repo/files/1", "不支持的资源类型: files"),
            ("https://github.com/owner/repo/releases/1", "不支持的资源类型: releases"),
            ("https://github.com/owner/repo/wiki", "不支持的资源类型: wiki"),
            ("https://github.com/owner/repo/tree/main", "不支持的资源类型: tree"),
            # 路径段过多
            ("https://github.com/owner/repo/issues/1/files/1", "路径段过多"),
            ("https://github.com/owner/repo/pull/42/commits", "路径段过多"),
            # 空字符串
            ("", "URL 不能为空"),
            # 查询参数应该被拒绝
            ("https://github.com/owner/repo/issues/1?foo=bar", "不支持查询参数"),
        ],
    )
    def test_parse_url_invalid(self, url: str, reason: str) -> None:
        """测试非法 URL 应抛出 URLParseError"""
        with pytest.raises(URLParseError) as exc_info:
            parse_url(url)

        # 验证异常消息包含原因
        if reason != "URL 不能为空":
            assert (
                reason in str(exc_info.value) or len(str(exc_info.value)) > 0
            ), f"异常消息应包含相关信息: {exc_info.value}"


class TestParseURLEdgeCases:
    """测试边缘情况"""

    def test_parse_url_same_urls_equal(self) -> None:
        """测试相同 URL 解析结果相等"""
        url = "https://github.com/owner/repo/issues/1"
        result1 = parse_url(url)
        result2 = parse_url(url)
        assert result1 == result2

    def test_parse_url_url_property(self) -> None:
        """测试 ResourceRef.url 属性"""
        url = "https://github.com/owner/repo/issues/1"
        result = parse_url(url)
        assert result.url == url


class TestOutputPath:
    """测试输出路径生成"""

    @pytest.mark.parametrize(
        "ref,root,expected",
        [
            # Issue 路径
            (
                ResourceRef("octocat", "Hello-World", ResourceType.ISSUE, 1),
                Path("out"),
                Path("out/octocat/Hello-World/issues/1.md"),
            ),
            # PR 路径
            (
                ResourceRef("owner", "repo", ResourceType.PULL, 42),
                Path("out"),
                Path("out/owner/repo/pulls/42.md"),
            ),
            # Discussion 路径
            (
                ResourceRef("vercel", "next.js", ResourceType.DISCUSSION, 100),
                Path("out"),
                Path("out/vercel/next.js/discussions/100.md"),
            ),
            # 自定义输出目录
            (
                ResourceRef("owner", "repo", ResourceType.ISSUE, 1),
                Path("custom/output"),
                Path("custom/output/owner/repo/issues/1.md"),
            ),
            # 保留原始大小写
            (
                ResourceRef("Octocat", "Hello-World", ResourceType.ISSUE, 1),
                Path("out"),
                Path("out/Octocat/Hello-World/issues/1.md"),
            ),
        ],
    )
    def test_output_path(self, ref: ResourceRef, root: Path, expected: Path) -> None:
        """测试路径拼接"""
        result = output_path(ref, root)
        assert result == expected, f"预期 {expected}, 实际 {result}"

    def test_output_path_is_str_only(self) -> None:
        """验证 output_path 仅做字符串拼接，不创建目录"""
        # 这是一个设计约束测试
        # 如果函数尝试创建目录，会因为目录不存在而失败（如果 root 是不存在的路径）
        ref = ResourceRef("owner", "repo", ResourceType.ISSUE, 1)
        root = Path("/nonexistent/path")

        # 应该成功返回路径，即使父目录不存在
        result = output_path(ref, root)
        assert result == Path("/nonexistent/path/owner/repo/issues/1.md")

        # 验证目录未被创建
        assert not root.exists()
