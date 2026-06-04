"""URL 解析模块"""

from pathlib import Path

from ..models.resource import ResourceRef, ResourceType
from ..errors import URLParseError


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
    # 检查空字符串
    if not url:
        raise URLParseError("URL 不能为空")

    # 检查查询参数
    if "?" in url:
        raise URLParseError("不支持查询参数")

    # 移除末尾斜杠
    url = url.rstrip("/")

    # 分割协议和其余部分
    protocol_parts = url.split("://")
    if len(protocol_parts) != 2:
        raise URLParseError("协议必须是 https")

    protocol, rest = protocol_parts
    if protocol != "https":
        raise URLParseError(f"协议必须是 https，实际为 {protocol}")

    # 分割域名和路径
    domain_parts = rest.split("/", 1)
    if len(domain_parts) != 2:
        raise URLParseError("缺少路径")

    domain, path = domain_parts
    if domain != "github.com":
        raise URLParseError(f"域名必须是 github.com，实际为 {domain}")

    # 解析路径段
    segments = path.split("/")
    if len(segments) != 4:
        raise URLParseError("路径格式错误")

    owner, repo, resource_type_str, number_str = segments

    # 验证 number 是正整数
    if not number_str:
        raise URLParseError("编号不能为空")

    if not number_str.isdigit():
        raise URLParseError("编号必须是数字")

    number = int(number_str)
    if number <= 0:
        raise URLParseError("编号必须是正整数")

    # 映射资源类型
    resource_type = _RESOURCE_TYPE_MAP.get(resource_type_str)
    if resource_type is None:
        raise URLParseError(f"不支持的资源类型: {resource_type_str}")

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
    # 映射类型到路径
    type_path = ref.type.value

    return root / ref.owner / ref.repo / type_path / f"{ref.number}.md"


__all__ = ["parse_url", "output_path"]