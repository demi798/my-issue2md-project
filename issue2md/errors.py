"""语义化退出码与自定义异常。

本模块是项目「明确性原则」的集中体现：
- 所有可预期的失败场景映射到一个明确的退出码，便于流水线判断。
- 所有异常显式定义，绝不静默吞掉（宪法第三条 3.1）。

退出码约定（与 ``specs/spec.md`` §1.5 保持一致）：

====  =========================================================
Code  含义
====  =========================================================
0     成功
1     参数错误（URL 格式不合法、参数冲突、缺少必填项）
2     网络 / API 错误（404、5xx、限流重试仍失败、网络中断）
3     文件 IO 错误（无法创建目录、无法写入文件、磁盘满）
4     鉴权错误（Token 无效、无权限访问私有仓库）
====  =========================================================
"""

from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    """语义化退出码枚举。

    使用 IntEnum 使其可直接作为 ``sys.exit`` 参数，
    同时具备 ``ExitCode.AUTH_ERROR`` 这样的自描述名称。
    """

    SUCCESS = 0
    PARAM_ERROR = 1
    NETWORK_API_ERROR = 2
    IO_ERROR = 3
    AUTH_ERROR = 4


class Issue2mdError(Exception):
    """所有 issue2md 自定义异常的基类。

    每个子类应通过 ``exit_code`` 类属性声明其对应的退出码，
    使 ``cli.py`` 顶层错误处理可统一映射。
    """

    exit_code: ExitCode = ExitCode.PARAM_ERROR


class URLParseError(Issue2mdError):
    """URL 格式不合法或类型不支持。"""

    exit_code = ExitCode.PARAM_ERROR


class GithubAPIError(Issue2mdError):
    """GitHub API 调用失败（网络/HTTP 错误、404、5xx 等）。"""

    exit_code = ExitCode.NETWORK_API_ERROR


class RateLimitError(GithubAPIError):
    """触发 GitHub 限流且重试后仍失败。"""

    exit_code = ExitCode.NETWORK_API_ERROR


class AuthError(Issue2mdError):
    """Token 无效或权限不足。"""

    exit_code = ExitCode.AUTH_ERROR


class FileIOError(Issue2mdError):
    """输出目录创建或文件写入失败。"""

    exit_code = ExitCode.IO_ERROR
