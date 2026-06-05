"""issue2md 错误消息常量"""

from __future__ import annotations

# 鉴权
TOKEN_EMPTY = "Token 不能为空"
TOKEN_TOO_SHORT = "Token 长度必须至少 20 个字符"
TOKEN_INVALID_CHARS = "Token 包含非法字符"
INVALID_TOKEN = "Invalid token (HTTP {})"
INSUFFICIENT_PERMISSIONS = "Insufficient permissions (HTTP {})"

# 限流
MISSING_RATE_LIMIT_RESET = "Missing X-RateLimit-Reset header"
INVALID_RATE_LIMIT_RESET = "Invalid X-RateLimit-Reset header: {}"
RATE_LIMIT_RESET_TOO_FAR = "Rate limit reset too far in future: {}s"
RATE_LIMIT_EXCEEDED = "Rate limit exceeded (HTTP {})"

# GitHub API
RESOURCE_NOT_FOUND = "Resource not found (HTTP {})"
GITHUB_SERVER_ERROR = "GitHub server error: {}"
UNEXPECTED_STATUS = "Unexpected status: {}"
NETWORK_ERROR = "Network error: {}"
INVALID_JSON_RESPONSE = "Invalid JSON response: {}"
DISCUSSION_NOT_FOUND = "Discussion not found or not enabled: {}"
GRAPHQL_ERROR = "GraphQL error: {}"
DISCUSSION_NOT_FOUND_SIMPLE = "Discussion not found"

# 文件 IO
FILE_NOT_FOUND = "File not found: {}"
PERMISSION_DENIED = "Permission denied: {}"
FILE_READ_FAILED = "Failed to read file {}: {}"
FILE_WRITE_FAILED = "Failed to write file {}: {}"

# URL 解析
URL_EMPTY = "URL 不能为空"
URL_QUERY_NOT_SUPPORTED = "不支持查询参数"
URL_PROTOCOL_INVALID = "协议必须是 https"
URL_PROTOCOL_MISMATCH = "协议必须是 https，实际为 {}"
URL_PATH_MISSING = "缺少路径"
URL_DOMAIN_MISMATCH = "域名必须是 github.com，实际为 {}"
URL_PATH_FORMAT_INVALID = "路径格式错误"
URL_NUMBER_EMPTY = "编号不能为空"
URL_NUMBER_NOT_DIGIT = "编号必须是数字"
URL_NUMBER_NOT_POSITIVE = "编号必须是正整数"
URL_RESOURCE_TYPE_UNSUPPORTED = "不支持的资源类型: {}"

# 限流 header / 环境变量
INVALID_RATE_LIMIT_REMAINING = "Invalid X-RateLimit-Remaining header: {}"
ENV_FILE_READ_SKIPPED = "Failed to read .env file {}: {}"

__all__ = [
    "TOKEN_EMPTY",
    "TOKEN_TOO_SHORT",
    "TOKEN_INVALID_CHARS",
    "INVALID_TOKEN",
    "INSUFFICIENT_PERMISSIONS",
    "MISSING_RATE_LIMIT_RESET",
    "INVALID_RATE_LIMIT_RESET",
    "RATE_LIMIT_RESET_TOO_FAR",
    "RATE_LIMIT_EXCEEDED",
    "RESOURCE_NOT_FOUND",
    "GITHUB_SERVER_ERROR",
    "UNEXPECTED_STATUS",
    "NETWORK_ERROR",
    "INVALID_JSON_RESPONSE",
    "DISCUSSION_NOT_FOUND",
    "GRAPHQL_ERROR",
    "DISCUSSION_NOT_FOUND_SIMPLE",
    "FILE_NOT_FOUND",
    "PERMISSION_DENIED",
    "FILE_READ_FAILED",
    "FILE_WRITE_FAILED",
    "URL_EMPTY",
    "URL_QUERY_NOT_SUPPORTED",
    "URL_PROTOCOL_INVALID",
    "URL_PROTOCOL_MISMATCH",
    "URL_PATH_MISSING",
    "URL_DOMAIN_MISMATCH",
    "URL_PATH_FORMAT_INVALID",
    "URL_NUMBER_EMPTY",
    "URL_NUMBER_NOT_DIGIT",
    "URL_NUMBER_NOT_POSITIVE",
    "URL_RESOURCE_TYPE_UNSUPPORTED",
    "INVALID_RATE_LIMIT_REMAINING",
    "ENV_FILE_READ_SKIPPED",
]
