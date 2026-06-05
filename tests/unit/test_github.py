"""GitHub API 单元测试 - Token 验证和响应处理"""

from unittest.mock import Mock, patch

import pytest

from issue2md.core.github import _handle_response, validate_token
from issue2md.errors import AuthError, GithubAPIError, RateLimitError


class TestValidateToken:
    """测试 Token 验证"""

    @pytest.mark.parametrize(
        "token",
        [
            "",  # 空字符串
            "   ",  # 仅空格
            "\t",  # 仅制表符
            "\n",  # 仅换行符
        ],
    )
    def test_validate_token_empty_string(self, token: str) -> None:
        """空字符串应抛出 AuthError"""
        with pytest.raises(AuthError) as exc_info:
            validate_token(token)

        assert "Token 不能为空" in str(exc_info.value) or "无效" in str(exc_info.value)

    @pytest.mark.parametrize(
        "token",
        [
            "a",  # 1 字符
            "short",  # 5 字符
            "way_too_short",  # 13 字符
            "x" * 19,  # 19 字符
            "abc123",  # 6 字符
        ],
    )
    def test_validate_token_too_short(self, token: str) -> None:
        """长度 < 20 应抛出 AuthError"""
        with pytest.raises(AuthError) as exc_info:
            validate_token(token)

        assert "长度" in str(exc_info.value) or "20" in str(exc_info.value)

    @pytest.mark.parametrize(
        "token",
        [
            "x" * 20,  # 正好 20 字符
            "x" * 40,  # 40 字符（标准 PAT 长度）
            "x" * 60,  # 60 字符
            "ghp_" + "x" * 36,  # 标准格式
            "valid_token_with_length_1234567890",  # 合法字符串
        ],
    )
    def test_validate_token_valid(self, token: str) -> None:
        """长度 >= 20 的合法 Token 不应抛出异常"""
        # 不应抛出任何异常
        validate_token(token)


class TestHandleResponse:
    """测试 HTTP 响应处理"""

    def test_handle_response_401(self) -> None:
        """401 → AuthError"""
        response = Mock()
        response.status_code = 401
        response.headers = {}

        with pytest.raises(AuthError) as exc_info:
            _handle_response(response, token=None)

        assert "Invalid token" in str(exc_info.value) or "鉴权" in str(exc_info.value)

    def test_handle_response_403_non_rate_limit(self) -> None:
        """403（非限流）→ AuthError"""
        response = Mock()
        response.status_code = 403
        response.headers = {"X-RateLimit-Remaining": "100"}

        with pytest.raises(AuthError) as exc_info:
            _handle_response(response, token=None)

        assert "权限" in str(exc_info.value) or "Insufficient" in str(exc_info.value)

    def test_handle_response_404(self) -> None:
        """404 → GithubAPIError"""
        response = Mock()
        response.status_code = 404
        response.headers = {}

        with pytest.raises(GithubAPIError) as exc_info:
            _handle_response(response, token=None)

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.parametrize("status_code", [500, 502, 503, 504])
    def test_handle_response_5xx(self, status_code: int) -> None:
        """5xx → GithubAPIError"""
        response = Mock()
        response.status_code = status_code
        response.headers = {}

        with pytest.raises(GithubAPIError) as exc_info:
            _handle_response(response, token=None)

        assert str(status_code) in str(exc_info.value)

    def test_handle_response_rate_limit_detected(self) -> None:
        """X-RateLimit-Remaining=0 → 应检测到限流"""
        current_time = 1700000000  # 2023-11-14 22:13:20 UTC
        reset_time = current_time + 300  # 5 分钟后

        response = Mock()
        response.status_code = 200
        response.headers = {
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(reset_time),
        }

        with (
            patch("issue2md.core.github.time.time", return_value=current_time),
            patch("issue2md.core.github.time.sleep"),
        ):
            # 函数不应抛出异常，只是标记需要重试
            _handle_response(response, token=None)

    def test_handle_response_rate_limit_wait_too_long(self) -> None:
        """reset - now > 600 秒 → RateLimitError"""
        current_time = 1700000000
        reset_time = current_time + 700  # 超过 600 秒

        response = Mock()
        response.status_code = 200
        response.headers = {
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(reset_time),
        }

        with pytest.raises(RateLimitError) as exc_info:
            with patch("issue2md.core.github.time.time", return_value=current_time):
                _handle_response(response, token=None)

        assert "700" in str(exc_info.value) or "too far" in str(exc_info.value)

    def test_handle_response_rate_limit_exactly_600(self) -> None:
        """reset - now = 600 秒 → 应允许等待"""
        current_time = 1700000000
        reset_time = current_time + 600

        response = Mock()
        response.status_code = 200
        response.headers = {
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(reset_time),
        }

        with (
            patch("issue2md.core.github.time.time", return_value=current_time),
            patch("issue2md.core.github.time.sleep"),
        ):
            # 不应抛出异常
            _handle_response(response, token=None)

    def test_handle_response_success_no_rate_limit(self) -> None:
        """正常响应且未限流 → 不应抛出异常"""
        response = Mock()
        response.status_code = 200
        response.headers = {"X-RateLimit-Remaining": "100"}

        # 不应抛出异常
        _handle_response(response, token=None)

    def test_handle_response_429_rate_limit(self) -> None:
        """429 状态码应同样触发限流逻辑"""
        current_time = 1700000000
        reset_time = current_time + 60

        response = Mock()
        response.status_code = 429
        response.headers = {
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(reset_time),
        }

        with (
            patch("issue2md.core.github.time.time", return_value=current_time),
            patch("issue2md.core.github.time.sleep"),
        ):
            # 不应抛出异常
            _handle_response(response, token=None)

    def test_handle_response_missing_remaining_header(self) -> None:
        """缺少 X-RateLimit-Remaining header → 默认不触发限流"""
        response = Mock()
        response.status_code = 200
        response.headers = {}

        # 不应抛出异常
        _handle_response(response, token=None)

    def test_handle_response_invalid_remaining_header(self) -> None:
        """X-RateLimit-Remaining 格式无效 → 不触发限流"""
        response = Mock()
        response.status_code = 200
        response.headers = {"X-RateLimit-Remaining": "invalid"}

        # 不应抛出异常（使用默认值 1）
        _handle_response(response, token=None)

    def test_handle_response_missing_reset_header(self) -> None:
        """X-RateLimit-Remaining=0 但缺少 X-RateLimit-Reset → 应抛异常"""
        response = Mock()
        response.status_code = 200
        response.headers = {"X-RateLimit-Remaining": "0"}

        with pytest.raises(RateLimitError):
            _handle_response(response, token=None)
