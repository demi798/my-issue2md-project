"""URL 解析、类型识别与输出路径推导。

本模块的职责边界（单一职责原则）：
- 输入：原始 URL 字符串 + 输出根目录配置。
- 输出：``ResourceRef`` 数据结构 + 目标 ``Path``。
- **不**负责任何 HTTP 请求或 Markdown 渲染。

支持的 URL 形态（与 ``specs/spec.md`` §1.1.3 一致）::

    https://github.com/<owner>/<repo>/issues/<number>
    https://github.com/<owner>/<repo>/pull/<number>
    https://github.com/<owner>/<repo>/discussions/<number>

设计要点
--------
- 使用 ``@dataclass(frozen=True)`` 保证解析结果不可变，便于在流水线中传递。
- 类型识别用 ``Enum`` 而非 magic string，避免 typo。
- 路径推导集中在 ``output_path``，避免散落多处。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse

from .errors import URLParseError


class ResourceType(str, Enum):
    """GitHub 资源类型枚举。

    继承 ``str`` 使其可直接用于字符串上下文（如目录名 ``"issues"``）。
    """

    ISSUE = "issues"
    PULL = "pulls"
    DISCUSSION = "discussions"


@dataclass(frozen=True)
class ResourceRef:
    """URL 解析后的不可变资源引用。

    Attributes:
        owner: 仓库所有者（用户名或组织名），保留原始大小写。
        repo: 仓库名，保留原始大小写。
        type: 资源类型（issue/pull/discussion）。
        number: Issue/PR/Discussion 编号。
    """

    owner: str
    repo: str
    type: ResourceType
    number: int


def parse_url(url: str) -> ResourceRef:
    """将 GitHub URL 解析为 ``ResourceRef``。

    Args:
        url: 待解析的 URL 字符串。

    Returns:
        解析后的 ``ResourceRef``。

    Raises:
        URLParseError: URL 格式不合法、协议非 https、域名非 github.com、
            路径不匹配已知资源类型、或 number 不是合法整数。
    """
    raise NotImplementedError("待 TDD 实现")


def output_path(ref: ResourceRef, root: Path) -> Path:
    """根据资源引用与输出根目录，推导最终 .md 文件路径。

    规则（spec.md §1.2.1）::

        <root>/<owner>/<repo>/<type>/<number>.md

    其中 ``<type>`` 取自 ``ResourceType.value``（如 ``"issues"``）。

    Args:
        ref: 已解析的资源引用。
        root: 输出根目录（默认由 CLI 传入 ``./out``）。

    Returns:
        最终 ``.md`` 文件的绝对路径。

    Note:
        本函数仅做路径推导，不创建任何目录、不检查目录是否可写。
        目录创建由 ``cli.py`` 在写入前统一处理。
    """
    raise NotImplementedError("待 TDD 实现")
