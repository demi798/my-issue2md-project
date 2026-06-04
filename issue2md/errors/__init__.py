"""异常定义模块"""

from .exceptions import (
    Issue2mdError,
    URLParseError,
    AuthError,
    RateLimitError,
    GithubAPIError,
    FileIOError,
)

__all__ = [
    "Issue2mdError",
    "URLParseError",
    "AuthError",
    "RateLimitError",
    "GithubAPIError",
    "FileIOError",
]