"""issue2md — 将 GitHub Issue/PR/Discussion 转换为本地 Markdown 文件。

一个为自动化流水线设计的命令行工具。详见 ``specs/spec.md``。

公共 API
========
本包对外暴露的稳定符号通过 ``__all__`` 显式声明，其它符号视为内部实现细节。

- :class:`IssueRef` / :class:`PRRef` / :class:`DiscussionRef`
    URL 解析后的资源引用，含 owner/repo/number/type 信息。
- :class:`ExitCode`
    语义化退出码枚举（0=成功, 1=参数错误, 2=网络/API, 3=IO, 4=鉴权）。
- :func:`run`
    主入口（供测试或库形式调用），等价于 CLI 的 ``main``。
"""

from __future__ import annotations

__version__: str = "0.1.0.dev0"
__all__: list[str] = []  # 待模块逐步实现后填入
