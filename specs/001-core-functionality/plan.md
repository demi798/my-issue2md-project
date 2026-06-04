# issue2md 技术实现方案

> **Version:** 1.0
> **Status:** Draft
> **Created:** 2026-06-04
> **Based on:** specs/001-core-functionality/spec.md
> **Aligned with:** constitution.md, api-sketch.md

---

## 1. 技术上下文总结

### 1.1 技术栈选型

| 组件 | 选择 | 理由（符合宪法第一条简单性原则） |
|------|------|----------------------------------|
| **语言** | Python >= 3.11 | 支持最新类型注解特性（`|` 联合类型、`Self` 等） |
| **Web框架** | 标准库 `http.server` | 避免引入 Flask/Django 等外部框架 |
| **HTTP客户端** | `requests` | spec.md §2.3 明确要求，最稳定成熟的 HTTP 库 |
| **GitHub API** | REST API v3 (Issue/PR) + GraphQL v4 (Discussion) | Discussion 必须用 GraphQL，其他用 REST |
| **Markdown 处理** | 纯字符串拼接 | 不引入第三方模板引擎 |
| **数据存储** | 无（实时 API 拉取） | spec.md §2.3 明确不需要数据库 |
| **前端序列化** | `PyYAML` | 用于 frontmatter 的 YAML 格式 |

### 1.2 依赖约束（严格遵循）

**运行时依赖**（仅两个）：
```toml
dependencies = [
    "requests>=2.31.0",
    "pyyaml>=6.0.0"
]
```

**开发依赖**：
```toml
dev-dependencies = [
    "pytest>=7.4.0",
    "pytest-mock>=3.12.0",
    "pytest-httpserver>=1.0.0",  # 集成测试 mock GitHub API
    "mypy>=1.5.0",
    "ruff>=0.1.0",
    "black>=23.7.0"
]
```

**明确不引入**（违反宪法第一条）：
- ❌ `PyGithub` - 过度抽象，违反简单性原则
- ❌ `httpx` - requests 已满足需求
- ❌ `rich` - CLI 输出到 stderr，不需要美化
- ❌ `Jinja2` - 字符串拼接即可满足需求

---

## 2. "合宪性"审查

对照 `constitution.md` 逐条验证：

### 2.1 第一条：简单性原则 ✅

| 条款 | 验证 |
|------|------|
| 1.1 YAGNI | ✅ 仅实现 spec.md 明确要求的功能，不实现图片下载、增量同步、Enterprise 支持等 |
| 1.2 标准库优先 | ✅ 使用 `pathlib.Path`、`dataclasses`、`datetime`、`enum` 等标准库 |
| 1.3 反过度工程 | ✅ 使用 `@dataclass(frozen=True)` 而非复杂继承体系；函数式风格优于类 |

### 2.2 第二条：测试先行铁律 ✅

| 条款 | 验证 |
|------|------|
| 2.1 TDD 循环 | ✅ 实现顺序遵循 api-sketch.md §6 优先级，每模块从失败测试开始 |
| 2.2 pytest 优先 | ✅ 所有测试使用 pytest，充分利用 `parametrize` 覆盖 AC1-AC10 |
| 2.3 拒绝过度 Mock | ✅ 集成测试使用 `pytest-httpserver` 模拟真实 HTTP 响应 |

### 2.3 第三条：明确性原则 ✅

| 条款 | 验证 |
|------|------|
| 3.1 异常处理 | ✅ 所有异常显式抛出并带语义化退出码，使用 `raise ... from err` 链式追踪 |
| 3.2 无全局变量 | ✅ 所有状态通过函数参数注入，Token 通过 CLI 参数传递 |
| 3.3 类型注解 | ✅ 所有公共 API 完整类型注解，通过 mypy 静态检查 |

### 2.4 第四条：Pythonic 代码风格 ✅

| 条款 | 验证 |
|------|------|
| 4.1 命名规范 | ✅ 函数 `snake_case`，类 `PascalCase`，常量 `UPPER_SNAKE_CASE` |
| 4.2 列表推导 | ✅ 评论合并、标签过滤使用列表推导式 |
| 4.3 上下文管理器 | ✅ 文件写入使用 `path.write_text()`（内部使用 `with`） |
| 4.4 数据类 | ✅ 所有跨模块数据结构使用 `@dataclass(frozen=True)` |

### 2.5 第五条：依赖管理原则 ✅

| 条款 | 验证 |
|------|------|
| 5.1 虚拟环境 | ✅ 通过 `pyproject.toml` 管理，Makefile 定义 `make install` |
| 5.2 依赖锁定 | ✅ 使用 `pip freeze` 或 Poetry 生成 `requirements.txt` |
| 5.3 安全审计 | ✅ Makefile 添加 `make audit` 使用 `pip-audit` |

---

## 3. 项目结构细化

### 3.1 最终目录结构

```
issue2md/
├── issue2md/                          # 主源代码包
│   ├── __init__.py                    # 包初始化，导出核心类/函数
│   ├── __main__.py                    # CLI 入口（`python -m issue2md`）
│   ├── cli/                           # CLI 层
│   │   ├── __init__.py
│   │   ├── main.py                    # `main()` 函数，参数解析与编排
│   │   └── args.py                    # argparse 配置（可选，可合入 main）
│   ├── core/                          # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── parser.py                  # URL 解析 → ResourceRef
│   │   ├── github.py                  # API 拉取 → IssueData/DiscussionData
│   │   └── converter.py               # 数据渲染 → Markdown 字符串
│   ├── models/                        # 数据模型（跨模块共享）
│   │   ├── __init__.py
│   │   ├── resource.py                # ResourceRef, ResourceType
│   │   ├── issue.py                   # IssueData, Comment, Label
│   │   └── discussion.py              # DiscussionData
│   └── errors/                        # 自定义异常
│       ├── __init__.py
│       └── exceptions.py              # Issue2mdError 基类 + 子类
├── tests/                             # 测试代码
│   ├── conftest.py                    # pytest fixtures（共享 mock 数据）
│   ├── unit/                          # 单元测试
│   │   ├── test_parser.py
│   │   ├── test_converter.py
│   │   └── test_errors.py
│   └── integration/                   # 集成测试
│       ├── test_github_issue.py
│       ├── test_github_pull.py
│       └── test_github_discussion.py
├── specs/                             # 功能规格文档
│   └── 001-core-functionality/
│       ├── spec.md
│       └── api-sketch.md
├── pyproject.toml                     # 项目配置与依赖
├── Makefile                           # 构建脚本
├── README.md                          # 项目说明
├── LICENSE                            # 开源协议
└── .gitignore
```

### 3.2 模块依赖关系

```
cli/
  ├─> models/      （ResourceRef 类型）
  ├─> core/parser  （parse_url, output_path）
  ├─> core/github  （fetch, validate_token）
  ├─> core/converter （render）
  └─> errors/      （异常处理）

core/parser
  ├─> models/      （ResourceRef）

core/github
  ├─> models/      （ResourceRef, IssueData, DiscussionData）
  └─> errors/      （AuthError, RateLimitError, GithubAPIError）

core/converter
  ├─> models/      （IssueData, DiscussionData）

models/
  └─> errors/      （无依赖）
```

**设计原则**：
- 单向依赖：CLI → Core → Models，避免循环引用
- 包内聚：数据模型独立，可在任何模块使用
- 错误层独立：异常定义集中，便于统一处理

---

## 4. 核心数据结构

### 4.1 `models/resource.py` - 资源引用

```python
from enum import Enum
from dataclasses import dataclass

class ResourceType(str, Enum):
    ISSUE = "issues"
    PULL = "pulls"
    DISCUSSION = "discussions"

@dataclass(frozen=True)
class ResourceRef:
    """GitHub 资源的引用标识，解析自 URL。"""
    owner: str       # 仓库所有者（保留原始大小写）
    repo: str        # 仓库名（保留原始大小写）
    type: ResourceType
    number: int      # Issue/PR/Discussion 编号

    @property
    def url(self) -> str:
        """重构为完整 GitHub URL。"""
        return f"https://github.com/{self.owner}/{self.repo}/{self.type}/{self.number}"
```

### 4.2 `models/issue.py` - Issue/PR 数据

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Self
from .resource import ResourceRef

@dataclass(frozen=True)
class Label:
    """Issue/PR 的标签。"""
    name: str
    color: str | None = None

@dataclass(frozen=True)
class Comment:
    """通用评论结构。"""
    author: str
    body: str
    created_at: datetime

@dataclass(frozen=True)
class IssueData:
    """Issue 或 Pull Request 的完整数据。"""
    ref: ResourceRef
    title: str
    state: str                       # "open" | "closed" | "merged"
    author: str
    body: str                        # GitHub 返回的 markdown 原文
    created_at: datetime
    updated_at: datetime
    labels: list[Label] = []
    comments: list[Comment] = []     # 已按 created_at 升序、已分页合并
    # PR 专用字段，Issue 中为 None
    draft: bool | None = None
    merged: bool | None = None
    mergeable: bool | None = None

    @property
    def comments_count(self) -> int:
        """返回真实评论总数（用于 frontmatter）。"""
        return len(self.comments)

    @property
    def type(self) -> str:
        """返回资源类型字符串。"""
        return "issue" if self.ref.type == ResourceType.ISSUE else "pull"
```

### 4.3 `models/discussion.py` - Discussion 数据

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Self
from .issue import Comment, Label
from .resource import ResourceRef

@dataclass(frozen=True)
class DiscussionData:
    """Discussion 的完整数据。"""
    ref: ResourceRef
    title: str
    author: str
    body: str
    created_at: datetime
    updated_at: datetime
    category: str                    # Discussion 分类名
    labels: list[Label] = []
    comments: list[Comment] = []     # GraphQL 翻页后合并
    answer_chosen: bool = False

    @property
    def comments_count(self) -> int:
        """返回真实评论总数（用于 frontmatter）。"""
        return len(self.comments)

    @property
    def type(self) -> str:
        """返回资源类型字符串。"""
        return "discussion"
```

### 4.4 `errors/exceptions.py` - 异常定义

```python
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
```

---

## 5. 接口设计

### 5.1 对外暴露的关键类/函数

`issue2md/__init__.py` 导出：

```python
# 资源解析
from .core.parser import parse_url, output_path

# 数据获取
from .core.github import fetch, validate_token

# 数据渲染
from .core.converter import render

# 类型
from .models.resource import ResourceRef, ResourceType
from .models.issue import IssueData, Comment, Label
from .models.discussion import DiscussionData

# 异常
from .errors.exceptions import (
    Issue2mdError,
    URLParseError,
    AuthError,
    RateLimitError,
    GithubAPIError,
    FileIOError,
)
```

### 5.2 CLI 入口接口

`__main__.py` / `cli/main.py`：

```python
import sys
from argparse import ArgumentParser

def parse_args(args: list[str] | None = None) -> Namespace:
    """解析命令行参数。"""
    parser = ArgumentParser(
        prog="issue2md",
        description="Convert GitHub Issues/PRs/Discussions to Markdown files.",
    )
    parser.add_argument(
        "urls",
        nargs="*",
        help="One or more GitHub Issue/PR/Discussion URLs",
    )
    parser.add_argument(
        "-f", "--from-file",
        type=Path,
        help="Read URLs from file (one per line, # comments ignored)",
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("out"),
        help="Output root directory (default: ./out)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite existing files (default behavior in v1)",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue processing next URL on error",
    )
    parser.add_argument(
        "--max-comments",
        type=int,
        default=0,
        help="Limit comments per resource (0 = unlimited)",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="GitHub token (falls back to GITHUB_TOKEN env var)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed error tracebacks",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="issue2md 1.0.0",
    )
    return parser.parse_args(args)

def main(args: list[str] | None = None) -> int:
    """CLI 主入口，返回语义化退出码。"""
    try:
        namespace = parse_args(args)
        # ... 编排逻辑
        return 0
    except Issue2mdError as e:
        print(e, file=sys.stderr)
        return e.exit_code
    except Exception as e:
        print(f"[FATAL] Unexpected error: {e}", file=sys.stderr)
        if namespace.verbose:
            raise
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

---

## 6. 实现优先级（TDD 推进顺序）

| 阶段 | 模块 | 第一个失败测试 | 验收标准 |
|------|------|----------------|----------|
| **P0** | `models/resource.py` | `ResourceRef.url` 属性返回正确 URL | dataclass 定义，frozen=True |
| **P0** | `errors/exceptions.py` | 各异常类 `exit_code` 属性正确 | 继承自 Issue2mdError |
| **P0** | `core/parser.parse_url` | AC6: 非法 URL 抛 `URLParseError` | 正则解析，返回 ResourceRef |
| **P0** | `core/parser.output_path` | AC1: 路径拼接正确 | 字符串操作，不创建目录 |
| **P1** | `core/github.validate_token` | Token 格式校验 | 空/短字符抛 AuthError |
| **P1** | `core/github.fetch (Issue)` | mock REST API 返回 IssueData | 分页处理，评论排序 |
| **P1** | `core/converter.render_frontmatter` | fixture → YAML frontmatter | PyYAML 序列化 |
| **P1** | `core/converter.render_body` | fixture → Markdown 正文 | 字符串拼接，评论截断 |
| **P2** | `cli.main._load_url_list` | 含注释/空行/行内注释的输入 | 文件读取，行过滤 |
| **P2** | `cli.main._dedup` | AC9: 重复 URL 仅保留首次 | set 去重 |
| **P2** | `core/github.fetch (PR)` | PR fixture，merged 字段填充 | 复用 IssueData，填充 PR 专用字段 |
| **P3** | `core/github.fetch (Discussion)` | GraphQL mock，递归翻页 | queries.py 模块 |
| **P3** | `cli.main.run` | AC5: 批量 + continue-on-error | 错误汇总，退出码计算 |

---

## 7. 限流处理实现

### 7.1 策略流程图

```
收到 HTTP 响应
    │
    ├─ X-RateLimit-Remaining: 0 ?
    │   ├─ Yes → 读取 X-RateLimit-Reset
    │   │         ├─ reset - now > 600 秒 ?
    │   │         │   ├─ Yes → 抛 RateLimitError
    │   │         │   └─ No  → sleep, 重试一次
    │   │         │              └─ 仍失败 → RateLimitError
    │   │         └─ 记录等待秒数到 stderr
    │   └─ No  → 继续处理
    │
    ├─ HTTP 状态码映射
    │   ├─ 401 → AuthError
    │   ├─ 403 → AuthError (非限流)
    │   ├─ 404 → GithubAPIError
    │   ├─ 429 → 同限流处理
    │   ├─ 5xx → GithubAPIError
    │   └─ 2xx → 正常
    │
    └─ 网络异常 → GithubAPIError
```

### 7.2 代码示例（`core/github.py`）

```python
import time
from requests import Response

def _handle_response(response: Response, token: str | None) -> None:
    """处理 GitHub API 响应，抛出语义化异常。"""
    remaining = int(response.headers.get("X-RateLimit-Remaining", "1"))

    # 限流处理
    if remaining == 0:
        reset_ts = int(response.headers.get("X-RateLimit-Reset", "0"))
        wait_seconds = reset_ts - int(time.time())
        if wait_seconds > 600:
            raise RateLimitError(f"Rate limit reset too far in future: {wait_seconds}s")

        print(f"[INFO] rate-limited, waiting {wait_seconds}s until reset...", file=sys.stderr)
        time.sleep(wait_seconds)

        # 重试逻辑由调用者实现
        return

    # 状态码映射
    if response.status_code == 401:
        raise AuthError("Invalid token")
    elif response.status_code == 403:
        raise AuthError("Insufficient permissions")
    elif response.status_code == 404:
        raise GithubAPIError("Resource not found")
    elif response.status_code >= 500:
        raise GithubAPIError(f"GitHub server error: {response.status_code}")
    elif not response.ok:
        raise GithubAPIError(f"Unexpected status: {response.status_code}")
```

---

## 8. 验收测试计划

### 8.1 单元测试（pytest + parametrize）

```python
# tests/unit/test_parser.py
import pytest
from issue2md.core.parser import parse_url
from issue2md.errors import URLParseError

@pytest.mark.parametrize("url,expected", [
    ("https://github.com/octocat/Hello-World/issues/1",
     ResourceRef("octocat", "Hello-World", ResourceType.ISSUE, 1)),
    ("https://github.com/owner/repo/pull/42",
     ResourceRef("owner", "repo", ResourceType.PULL, 42)),
    ("https://github.com/vercel/next.js/discussions/100",
     ResourceRef("vercel", "next.js", ResourceType.DISCUSSION, 100)),
])
def test_parse_url_valid(url: str, expected: ResourceRef):
    assert parse_url(url) == expected

@pytest.mark.parametrize("url", [
    "http://github.com/owner/repo/issues/1",      # 非https
    "https://gitlab.com/owner/repo/issues/1",     # 非github.com
    "https://github.com/owner/repo/commits/abc",  # 非目标资源
    "https://github.com/owner/repo/issues/abc",   # number非数字
])
def test_parse_url_invalid(url: str):
    with pytest.raises(URLParseError):
        parse_url(url)
```

### 8.2 集成测试（pytest-httpserver）

```python
# tests/integration/test_github_issue.py
import json
from pytest_httpserver import HTTPServer
from issue2md.core.github import fetch

def test_fetch_issue_success(httpserver: HTTPServer):
    # Mock GitHub API 响应
    httpserver.expect_request("/repos/octocat/Hello-World/issues/1").respond_with_json({
        "title": "Test Issue",
        "state": "open",
        "user": {"login": "octocat"},
        "body": "Test body",
        "created_at": "2026-01-02T03:04:05Z",
        "updated_at": "2026-06-01T07:08:09Z",
        "labels": [{"name": "bug", "color": "d73a4a"}],
        "pull_request": None,  # 标识为 Issue
    })

    ref = ResourceRef("octocat", "Hello-World", ResourceType.ISSUE, 1)
    data = fetch(ref, token=None)

    assert isinstance(data, IssueData)
    assert data.title == "Test Issue"
    assert data.author == "octocat"
    assert len(data.labels) == 1
```

### 8.3 AC 场景覆盖矩阵

| AC | 测试文件 | 测试函数 |
|----|----------|----------|
| AC1 | `test_cli_integration.py` | `test_single_issue_success` |
| AC2 | `test_github_rate_limit.py` | `test_rate_limit_retry_once` |
| AC3 | `test_cli_integration.py` | `test_single_pull_success` |
| AC4 | `test_github_discussion.py` | `test_fetch_discussion_with_category` |
| AC5 | `test_cli_batch.py` | `test_batch_continue_on_error` |
| AC6 | `test_parser.py` | `test_parse_url_invalid` |
| AC7 | `test_github_auth.py` | `test_private_repo_without_token` |
| AC8 | `test_cli_io.py` | `test_readonly_directory` |
| AC9 | `test_cli_batch.py` | `test_url_deduplication` |
| AC10 | `test_converter.py` | `test_render_max_comments_truncation` |

---

## 9. 构建与发布

### 9.1 Makefile 定义

```makefile
.PHONY: all test install format typecheck lint audit clean

all: test typecheck lint

test:
	pytest tests/ -v --cov=issue2md --cov-report=term-missing

install:
	pip install -e .

format:
	black issue2md tests
	isort issue2md tests

typecheck:
	mypy issue2md

lint:
	ruff check issue2md tests

audit:
	pip-audit

clean:
	rm -rf .pytest_cache .coverage .mypy_cache .ruff_cache out/
```

### 9.2 pyproject.toml 模板

```toml
[project]
name = "issue2md"
version = "1.0.0"
description = "Convert GitHub Issues/PRs/Discussions to Markdown files"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.31.0",
    "pyyaml>=6.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-mock>=3.12.0",
    "pytest-httpserver>=1.0.0",
    "pytest-cov>=4.1.0",
    "mypy>=1.5.0",
    "ruff>=0.1.0",
    "black>=23.7.0",
    "isort>=5.12.0",
    "pip-audit>=2.6.0",
]

[project.scripts]
issue2md = "issue2md.__main__:main"

[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --cov=issue2md --cov-report=term-missing"
```

---

## 10. 总结

本技术方案严格遵循 `constitution.md` 的所有原则：

1. **简单性**：仅实现 spec.md 要求的功能，依赖最小化（仅 requests + pyyaml）
2. **测试先行**：每个模块从失败测试开始，使用 pytest + parametrize 覆盖 AC1-AC10
3. **明确性**：异常显式处理，类型注解完整，无全局变量
4. **Pythonic**：使用 dataclass、pathlib、列表推导式等惯用法
5. **依赖管理**：通过 pyproject.toml 管理，Makefile 标准化操作

项目结构清晰，模块单向依赖，数据结构不可变，符合包内聚原则。实现优先级明确，遵循 TDD 推进顺序。

**下一步**：用户审阅本方案后，按照 §6 优先级开始 TDD 实现。