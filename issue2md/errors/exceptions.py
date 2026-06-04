"""issue2md 异常定义"""

from dataclasses import dataclass


class Issue2mdError(Exception):
    """所有 issue2md 异常的基类，带语义化退出码。"""
    exit_code: int = 1

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return f"[ERROR] {self.message}"


class URLParseError(Issue2mdError):
    """URL 解析失败（exit_code=1）。"""
    exit_code: int = 1


class AuthError(Issue2mdError):
    """鉴权失败（exit_code=4）。"""
    exit_code: int = 4


class RateLimitError(Issue2mdError):
    """限流且重试失败（exit_code=2）。"""
    exit_code: int = 2


class GithubAPIError(Issue2mdError):
    """GitHub API 错误（exit_code=2）。"""
    exit_code: int = 2


class FileIOError(Issue2mdError):
    """文件 IO 错误（exit_code=3）。"""
    exit_code: int = 3


__all__ = [
    "Issue2mdError",
    "URLParseError",
    "AuthError",
    "RateLimitError",
    "GithubAPIError",
    "FileIOError",
]