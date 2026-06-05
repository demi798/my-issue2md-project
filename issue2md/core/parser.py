"""URL 解析模块"""

from __future__ import annotations

from pathlib import Path

from ..errors import URLParseError
from ..errors.messages import (
    URL_DOMAIN_MISMATCH,
    URL_EMPTY,
    URL_NUMBER_EMPTY,
    URL_NUMBER_NOT_DIGIT,
    URL_NUMBER_NOT_POSITIVE,
    URL_PATH_FORMAT_INVALID,
    URL_PATH_MISSING,
    URL_PROTOCOL_INVALID,
    URL_PROTOCOL_MISMATCH,
    URL_QUERY_NOT_SUPPORTED,
    URL_RESOURCE_TYPE_UNSUPPORTED,
)
from ..models.resource import ResourceRef, ResourceType

# 资源类型映射
_RESOURCE_TYPE_MAP: dict[str, ResourceType] = {
    "issues": ResourceType.ISSUE,
    "pull": ResourceType.PULL,
    "discussions": ResourceType.DISCUSSION,
}


def parse_url(url: str) -> ResourceRef:
    """将 GitHub URL 解析为 ResourceRef。

    支持的 URL 格式：
        https://github.com/{owner}/{repo}/{issues|pull|discussions}/{number}

    Args:
        url: GitHub URL 字符串

    Returns:
        ResourceRef: 解析后的资源引用

    Raises:
        URLParseError: URL 格式不合法时抛出
    """
    if not url:
        raise URLParseError(URL_EMPTY)

    if "?" in url:
        raise URLParseError(URL_QUERY_NOT_SUPPORTED)

    url = url.rstrip("/")

    protocol_parts = url.split("://")
    if len(protocol_parts) != 2:
        raise URLParseError(URL_PROTOCOL_INVALID)

    protocol, rest = protocol_parts
    if protocol != "https":
        raise URLParseError(URL_PROTOCOL_MISMATCH.format(protocol))

    domain_parts = rest.split("/", 1)
    if len(domain_parts) != 2:
        raise URLParseError(URL_PATH_MISSING)

    domain, path = domain_parts
    if domain != "github.com":
        raise URLParseError(URL_DOMAIN_MISMATCH.format(domain))

    segments = path.split("/")
    if len(segments) != 4:
        raise URLParseError(URL_PATH_FORMAT_INVALID)

    owner, repo, resource_type_str, number_str = segments

    if not number_str:
        raise URLParseError(URL_NUMBER_EMPTY)

    if not number_str.isdigit():
        raise URLParseError(URL_NUMBER_NOT_DIGIT)

    number = int(number_str)
    if number <= 0:
        raise URLParseError(URL_NUMBER_NOT_POSITIVE)

    resource_type = _RESOURCE_TYPE_MAP.get(resource_type_str)
    if resource_type is None:
        raise URLParseError(URL_RESOURCE_TYPE_UNSUPPORTED.format(resource_type_str))

    return ResourceRef(
        owner=owner,
        repo=repo,
        type=resource_type,
        number=number,
    )


def output_path(ref: ResourceRef, root: Path) -> Path:
    """推导 .md 文件的最终磁盘路径。

    路径格式：<root>/<owner>/<repo>/<type>/<number>.md

    注意：
        - 仅做字符串拼接，不创建目录
        - 不检查可写性

    Args:
        ref: 资源引用
        root: 输出根目录

    Returns:
        Path: .md 文件的完整路径
    """
    type_path = ref.type.value

    return root / ref.owner / ref.repo / type_path / f"{ref.number}.md"


__all__ = ["parse_url", "output_path"]
