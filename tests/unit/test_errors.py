"""异常模块的单元测试"""

from issue2md.errors.exceptions import (AuthError, FileIOError, GithubAPIError,
                                        Issue2mdError, RateLimitError,
                                        URLParseError)


class TestIssue2mdError:
    """测试 Issue2mdError 基类"""

    def test_default_exit_code(self) -> None:
        """测试默认退出码为 1"""
        err = Issue2mdError("test message")
        assert err.exit_code == 1

    def test_message_attribute(self) -> None:
        """测试 message 属性可访问"""
        err = Issue2mdError("test message")
        assert err.message == "test message"

    def test_str_format(self) -> None:
        """测试字符串格式为 [ERROR] {message}"""
        err = Issue2mdError("test message")
        assert str(err) == "[ERROR] test message"

    def test_inheritance(self) -> None:
        """测试继承自 Exception"""
        err = Issue2mdError("test message")
        assert isinstance(err, Exception)


class TestURLParseError:
    """测试 URLParseError"""

    def test_exit_code(self) -> None:
        """测试退出码为 1"""
        err = URLParseError("URL 格式错误")
        assert err.exit_code == 1

    def test_inheritance(self) -> None:
        """测试继承自 Issue2mdError"""
        err = URLParseError("URL 格式错误")
        assert isinstance(err, Issue2mdError)
        assert isinstance(err, Exception)


class TestAuthError:
    """测试 AuthError"""

    def test_exit_code(self) -> None:
        """测试退出码为 4"""
        err = AuthError("Token 无效")
        assert err.exit_code == 4

    def test_inheritance(self) -> None:
        """测试继承自 Issue2mdError"""
        err = AuthError("Token 无效")
        assert isinstance(err, Issue2mdError)
        assert isinstance(err, Exception)


class TestRateLimitError:
    """测试 RateLimitError"""

    def test_exit_code(self) -> None:
        """测试退出码为 2"""
        err = RateLimitError("达到限流上限")
        assert err.exit_code == 2

    def test_inheritance(self) -> None:
        """测试继承自 Issue2mdError"""
        err = RateLimitError("达到限流上限")
        assert isinstance(err, Issue2mdError)
        assert isinstance(err, Exception)


class TestGithubAPIError:
    """测试 GithubAPIError"""

    def test_exit_code(self) -> None:
        """测试退出码为 2"""
        err = GithubAPIError("GitHub API 错误")
        assert err.exit_code == 2

    def test_inheritance(self) -> None:
        """测试继承自 Issue2mdError"""
        err = GithubAPIError("GitHub API 错误")
        assert isinstance(err, Issue2mdError)
        assert isinstance(err, Exception)


class TestFileIOError:
    """测试 FileIOError"""

    def test_exit_code(self) -> None:
        """测试退出码为 3"""
        err = FileIOError("文件写入失败")
        assert err.exit_code == 3

    def test_inheritance(self) -> None:
        """测试继承自 Issue2mdError"""
        err = FileIOError("文件写入失败")
        assert isinstance(err, Issue2mdError)
        assert isinstance(err, Exception)
