"""CLI 主入口"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from ..core import fetch, output_path, parse_url, render
from ..errors import FileIOError, Issue2mdError
from ..errors.messages import (
    ENV_FILE_READ_SKIPPED,
    FILE_NOT_FOUND,
    FILE_READ_FAILED,
    FILE_WRITE_FAILED,
    PERMISSION_DENIED,
)

# 非 Issue2mdError 的已知 CLI 运行时错误
_CLI_RUNTIME_ERRORS: tuple[type[BaseException], ...] = (
    AttributeError,
    KeyError,
    LookupError,
    RecursionError,
    RuntimeError,
    TypeError,
    ValueError,
)


def _handle_unexpected_error(error: BaseException, *, verbose: bool, label: str = "FATAL") -> int:
    """处理未预期的 CLI 异常：记录错误，verbose 模式下重新抛出。"""
    print(f"[{label}] Unexpected error: {error}", file=sys.stderr)
    if verbose:
        raise error
    return 1


def _handle_unexpected_url_error(
    url: str,
    error: BaseException,
    *,
    verbose: bool,
    errors: list[dict[str, Any]],
) -> None:
    """记录单个 URL 的未预期错误；verbose 模式下重新抛出。"""
    errors.append({"url": url, "exit_code": 1})
    print(f"[ERROR] Unexpected error: {error}", file=sys.stderr)
    if verbose:
        raise error


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """解析命令行参数。

    Args:
        args: 参数列表，默认为 sys.argv[1:]

    Returns:
        解析后的命名空间对象
    """
    parser = argparse.ArgumentParser(
        prog="issue2md",
        description="Convert GitHub Issues/PRs/Discussions to Markdown files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # 位置参数：URL 列表
    parser.add_argument(
        "urls",
        nargs="*",
        help="One or more GitHub Issue/PR/Discussion URLs",
    )

    # 从文件读取 URL
    parser.add_argument(
        "-f",
        "--from-file",
        type=Path,
        help="Read URLs from file (one per line, # comments ignored)",
    )

    # 输出目录
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("out"),
        help="Output root directory (default: ./out)",
    )

    # 强制覆盖
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite existing files (default behavior in v1)",
    )

    # 遇到错误继续处理
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue processing next URL on error",
    )

    # 限制评论数量
    parser.add_argument(
        "--max-comments",
        type=int,
        default=0,
        help="Limit comments per resource (0 = unlimited)",
    )

    # GitHub Token
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="GitHub token (falls back to GITHUB_TOKEN env var)",
    )

    # 详细输出
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed error tracebacks",
    )

    # 版本信息
    parser.add_argument(
        "--version",
        action="version",
        version="issue2md 1.0.0",
    )

    # 解析参数
    namespace = parser.parse_args(args)

    # 验证参数互斥性
    if namespace.urls and namespace.from_file:
        print("Warning: Both URLs and --from-file provided. Using URLs.", file=sys.stderr)

    return namespace


def main(args: list[str] | None = None) -> int:
    """CLI 主入口，返回语义化退出码。

    Args:
        args: 参数列表，默认为 sys.argv[1:]

    Returns:
        退出码：0=成功，1=参数错误，2=网络/API错误，3=文件IO错误，4=鉴权错误
    """
    namespace: argparse.Namespace | None = None
    try:
        namespace = parse_args(args)

        # 获取 Token
        token = namespace.token or get_github_token()

        # 加载 URL 列表
        url_list = load_urls(namespace.urls, namespace.from_file)

        # 去重
        url_list = dedup_urls(url_list)

        # 如果没有 URL，显示帮助
        if not url_list:
            print("Error: No URLs provided", file=sys.stderr)
            return 1

        # 处理所有 URL
        return process_urls(url_list, namespace, token)

    except Issue2mdError as e:
        print(e, file=sys.stderr)
        return e.exit_code
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user", file=sys.stderr)
        return 130
    except _CLI_RUNTIME_ERRORS as e:
        verbose = namespace is not None and namespace.verbose
        return _handle_unexpected_error(e, verbose=verbose)
    except Exception as e:
        # 兜底：捕获 MemoryError 等未列出的系统级异常
        verbose = namespace is not None and namespace.verbose
        return _handle_unexpected_error(e, verbose=verbose)


def get_github_token() -> str | None:
    """获取 GitHub Token。

    优先级：环境变量 GITHUB_TOKEN > .env 文件。

    Returns:
        Token 字符串；未配置时返回 None
    """
    token = os.environ.get("GITHUB_TOKEN")
    if token and token.strip():
        return token.strip()

    # 从当前工作目录向上查找 .env 文件
    for directory in [Path.cwd(), *Path.cwd().parents]:
        env_path = directory / ".env"
        if not env_path.is_file():
            continue
        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("export "):
                    line = line[7:].strip()
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                if key.strip() != "GITHUB_TOKEN":
                    continue
                value = value.strip()
                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]
                if value:
                    return value
        except OSError as err:
            print(
                f"[WARN] {ENV_FILE_READ_SKIPPED.format(env_path, err)}",
                file=sys.stderr,
            )
            continue

    return None


def load_urls(urls: list[str], from_file: Path | None) -> list[str]:
    """加载 URL 列表。

    Args:
        urls: 命令行直接提供的 URL 列表
        from_file: 从文件读取的 URL 文件路径

    Returns:
        URL 列表
    """
    if urls:
        return urls

    if from_file:
        return load_url_list(from_file)

    return []


def load_url_list(file_path: Path) -> list[str]:
    """从文件加载 URL 列表。

    Args:
        file_path: 文件路径

    Returns:
        URL 列表

    Raises:
        FileIOError: 文件读取失败
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 过滤空行、注释、行内注释
        url_list = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # 处理行内注释
            if "#" in line:
                line = line.split("#", 1)[0].strip()

            if line:
                url_list.append(line)

        return url_list

    except FileNotFoundError as err:
        raise FileIOError(FILE_NOT_FOUND.format(file_path)) from err
    except PermissionError as err:
        raise FileIOError(PERMISSION_DENIED.format(file_path)) from err
    except OSError as err:
        raise FileIOError(FILE_READ_FAILED.format(file_path, str(err))) from err


def dedup_urls(urls: list[str]) -> list[str]:
    """URL 去重，保持首次出现的顺序。

    Args:
        urls: 原始 URL 列表

    Returns:
        去重后的 URL 列表
    """
    seen = set()
    deduped = []

    for url in urls:
        if url not in seen:
            seen.add(url)
            deduped.append(url)

    return deduped


def process_urls(url_list: list[str], args: argparse.Namespace, token: str | None) -> int:
    """处理所有 URL。

    Args:
        url_list: URL 列表
        args: 命令行参数
        token: GitHub Token

    Returns:
        退出码
    """

    results = []
    errors: list[dict[str, Any]] = []

    for url in url_list:
        try:
            print(f"[INFO] Processing {url}", file=sys.stderr)

            # 解析 URL
            ref = parse_url(url)

            # 获取数据
            data = fetch(ref, token)

            # 渲染 Markdown
            markdown = render(data, args.max_comments)

            # 写入文件
            output_file = output_path(ref, args.output_dir)
            write_file(output_file, markdown)

            results.append({"url": url, "exit_code": 0})

        except Issue2mdError as e:
            errors.append({"url": url, "exit_code": e.exit_code})
            print(f"[ERROR] {e}", file=sys.stderr)

            if not args.continue_on_error:
                return e.exit_code

        except (KeyboardInterrupt, SystemExit):
            raise
        except _CLI_RUNTIME_ERRORS as e:
            _handle_unexpected_url_error(url, e, verbose=args.verbose, errors=errors)
            if not args.continue_on_error:
                return 1
        except Exception as e:
            # 兜底：捕获 MemoryError 等未列出的系统级异常
            _handle_unexpected_url_error(url, e, verbose=args.verbose, errors=errors)
            if not args.continue_on_error:
                return 1

    # 汇总结果
    if errors and args.continue_on_error:
        print(
            "\n[SUMMARY] processed={}, succeeded={}, failed={}".format(
                len(url_list), len(results), len(errors)
            ),
            file=sys.stderr,
        )

        for error in errors:
            print("[FAILED] {} → exit={}".format(error["url"], error["exit_code"]), file=sys.stderr)

        # 返回最严重的错误码
        max_error = max(int(error["exit_code"]) for error in errors)
        return int(max_error)  # 确保返回 int 类型

    return 0


def write_file(file_path: Path, content: str) -> None:
    """写入文件。

    Args:
        file_path: 文件路径
        content: 文件内容

    Raises:
        FileIOError: 文件写入失败
    """
    try:
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        file_path.write_text(content, encoding="utf-8")

        print(f"[INFO] Written to {file_path}", file=sys.stderr)

    except PermissionError as err:
        raise FileIOError(PERMISSION_DENIED.format(file_path)) from err
    except OSError as err:
        raise FileIOError(FILE_WRITE_FAILED.format(file_path, str(err))) from err


if __name__ == "__main__":
    sys.exit(main())
