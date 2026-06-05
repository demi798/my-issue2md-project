"""异常定义模块"""

from __future__ import annotations

from .exceptions import (AuthError, FileIOError, GithubAPIError, Issue2mdError,
                         RateLimitError, URLParseError)

__all__ = [
    "Issue2mdError",
    "URLParseError",
    "AuthError",
    "RateLimitError",
    "GithubAPIError",
    "FileIOError",
]
