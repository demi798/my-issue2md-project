# API Sketch — 核心模块对外接口草案

> **Scope:** `src/issue2md/parser.py`、`src/issue2md/github.py`、`src/issue2md/converter.py`
> **Status:** Sketch（作为 TDD 实现的契约参考，实现时签名可能微调）
> **Last Updated:** 2026-06-04
> **Related:** [`../spec.md`](../spec.md)

---

## 0. 设计原则回顾

依宪法「简单性」「明确性」「包内聚」原则：

- **每个模块单一职责**：模块边界即数据流边界（URL 字符串 → 数据结构 → Markdown 字符串 → 文件）。
- **数据结构不可变**：所有跨模块传递的数据使用 `@dataclass(frozen=True)`，避免下游意外修改。
- **异常显式**：每个模块抛出语义化的自定义异常（`URLParseError` / `GithubAPIError` / `FileIOError`），由 `cli.py` 统一映射到退出码。
- **类型注解完整**：所有公共函数签名带类型，便于 `mypy` 静态校验。

---

## 1. 数据流总览

```
                     ┌─────────────┐
   URL 字符串 ─────► │   parser    │ ──► ResourceRef
                     └─────────────┘                  ┌─────────────┐
                              │                       │   github    │
                              └──── ref + token ────► │             │ ──► IssueData | DiscussionData
                                                      └─────────────┘
                                                              │
                                                              ▼
                                                      ┌─────────────┐
                                                      │  converter  │ ──► str (Markdown)
                                                      └─────────────┘
                                                              │
                                                              ▼
                                                      ┌─────────────┐
                                                      │  cli (IO)   │ ──► 写入 .md 文件
                                                      └─────────────┘
```

---

## 2. `parser` 模块接口

### 2.1 数据结构

```python
class ResourceType(str, Enum):
    ISSUE = "issues"
    PULL = "pulls"
    DISCUSSION = "discussions"

@dataclass(frozen=True)
class ResourceRef:
    owner: str       # 仓库所有者（保留原始大小写）
    repo: str        # 仓库名（保留原始大小写）
    type: ResourceType
    number: int      # Issue/PR/Discussion 编号
```

### 2.2 公开函数

#### `parse_url(url: str) -> ResourceRef`

**职责**：将 GitHub URL 解析为 `ResourceRef`。

**输入**：
- `url: str` — 待解析的 URL 字符串。

**返回**：
- `ResourceRef` — 解析后的资源引用。

**异常**：
- `URLParseError`（exit_code=1）— 以下情形触发：
  - 协议不是 `https://`
  - 域名不是 `github.com`
  - 路径不匹配 `/{owner}/{repo}/{issues|pull|discussions}/{number}`
  - `number` 不是正整数
  - 末尾有不允许的额外路径段（如 `/files/123`）

**约定**：
- 末尾斜杠可选：`.../issues/123/` 合法。
- 不发任何网络请求，纯本地解析。

#### `output_path(ref: ResourceRef, root: Path) -> Path`

**职责**：推导 .md 文件的最终磁盘路径。

**输入**：
- `ref: ResourceRef`
- `root: Path` — 输出根目录（由 CLI 传入，默认 `./out`）。

**返回**：
- `Path` — 形如 `<root>/<owner>/<repo>/<type>/<number>.md` 的路径。

**约定**：
- **仅做字符串拼接**，不创建目录、不检查可写性。
- 路径中的 `owner` / `repo` 使用 URL 中的原始大小写。

---

## 3. `github` 模块接口

### 3.1 数据结构

```python
@dataclass(frozen=True)
class Comment:
    author: str
    body: str
    created_at: datetime

@dataclass(frozen=True)
class Label:
    name: str
    color: str | None = None

@dataclass(frozen=True)
class IssueData:
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

@dataclass(frozen=True)
class DiscussionData:
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
```

> **设计取舍**：`Issue` 与 `PR` 共用 `IssueData`，是因为两者字段重合度 > 90%，且 PR 专用字段（draft/merged/mergeable）用 `None` 占位不会引起渲染层分支爆炸。`Discussion` 字段差异较大（category / answer_chosen），独立结构更清晰。

### 3.2 公开函数

#### `fetch(ref: ResourceRef, token: str | None = None) -> IssueData | DiscussionData`

**职责**：根据资源引用拉取完整数据（含全量评论，自动分页）。

**输入**：
- `ref: ResourceRef` — 由 `parser.parse_url` 产出。
- `token: str | None` — GitHub Token；`None` 走匿名（60 次/小时）。

**返回**：
- `IssueData`（当 `ref.type` 为 ISSUE 或 PULL）
- `DiscussionData`（当 `ref.type` 为 DISCUSSION）

**异常**：
- `AuthError`（exit_code=4）— Token 无效（401）或权限不足（403 非限流）。
- `RateLimitError`（exit_code=2）— 限流且等待重试一次后仍失败。
- `GithubAPIError`（exit_code=2）— 其它 HTTP/网络错误：
  - 404：URL 不存在或 Discussion 未启用
  - 5xx：GitHub 服务端错误
  - 网络异常 / DNS 失败 / 超时

**约定**：
- 分页：REST 用 `per_page=100` + `Link` header；GraphQL 用 `comments(first: 100, after: $cursor)` 递归。
- 评论已按 `created_at` **升序**排序后返回。
- 限流处理：检测 `X-RateLimit-Remaining: 0`，读 `X-RateLimit-Reset`，等待 ≤ 600 秒后重试一次。

#### `validate_token(token: str) -> None`

**职责**：本地格式校验（不发请求）。

**输入**：
- `token: str` — 待校验的 Token 字符串。

**异常**：
- `AuthError`（exit_code=4）— Token 为空、长度 < 20、或含非 ASCII 可见字符。

---

## 4. `converter` 模块接口

### 4.1 公开函数

#### `render(data: IssueData | DiscussionData, *, max_comments: int = 0) -> str`

**职责**：将数据对象转换为完整 Markdown 文件内容（含 frontmatter）。

**输入**：
- `data: IssueData | DiscussionData` — 由 `github.fetch` 产出。
- `max_comments: int` — 评论截断阈值，`0` 表示全量。

**返回**：
- `str` — 完整 Markdown 内容（可直接 `path.write_text`）。

**异常**：
- `ValueError` — `max_comments` 为负数。

**约定**：
- frontmatter 中 `comments_count` 字段反映**真实**评论总数，与截断无关（spec.md AC10）。
- 评论计数从 1 开始：`### Comment 1 — @...`。
- 评论为 0 时仍输出 `## Comments (0)` 占位（结构稳定，便于脚本匹配）。

#### `render_frontmatter(data: IssueData | DiscussionData) -> str`

**职责**：仅生成 YAML frontmatter 区块。

**返回**：形如 `---\n...\n---\n` 的字符串。

**字段顺序**（spec.md §1.2.3）：

| 字段 | 类型 | 必填 | 备注 |
|---|---|---|---|
| `url` | str | ✓ | 完整 GitHub URL |
| `type` | str | ✓ | `issue` / `pull` / `discussion` |
| `owner` | str | ✓ | |
| `repo` | str | ✓ | |
| `number` | int | ✓ | |
| `title` | str | ✓ | YAML 双引号转义 |
| `state` | str | ✓ | `open` / `closed` / `merged` |
| `author` | str | ✓ | |
| `created_at` | str | ✓ | ISO 8601 UTC |
| `updated_at` | str | ✓ | ISO 8601 UTC |
| `labels` | list[str] | ✓ | 标签 name 列表 |
| `comments_count` | int | ✓ | 真实评论总数 |
| `fetched_at` | str | ✓ | 工具拉取时刻 |
| `category` | str | Discussion | 仅 Discussion |
| `answer_chosen` | bool | Discussion | 仅 Discussion |
| `draft` | bool | PR | 仅 PR |
| `merged` | bool | PR | 仅 PR |
| `mergeable` | bool\|null | PR | 仅 PR |

#### `render_body(data: IssueData | DiscussionData, *, max_comments: int = 0) -> str`

**职责**：生成正文部分（不含 frontmatter）。

**返回**：

```markdown
# <title>  [<state>]

<body>

---

## Comments (<count>)

### Comment 1 — @<author> · <created_at>

<comment body>

### Comment 2 — @<author> · <created_at>

<comment body>
```

---

## 5. 异常 → 退出码映射（参考）

完整定义见 `src/issue2md/errors.py`：

| 异常 | 退出码 | 主要触发模块 |
|---|---|---|
| `URLParseError` | 1 (PARAM_ERROR) | `parser.parse_url` |
| `AuthError` | 4 (AUTH_ERROR) | `github.fetch` / `github.validate_token` |
| `RateLimitError` | 2 (NETWORK_API_ERROR) | `github.fetch` |
| `GithubAPIError` | 2 (NETWORK_API_ERROR) | `github.fetch` |
| `FileIOError` | 3 (IO_ERROR) | `cli._write_file` |

`cli.main` 顶层 `except Issue2mdError` 统一捕获并打印 `[ERROR] ...` 到 stderr，返回对应退出码。

---

## 6. 实现优先级（建议的 TDD 推进顺序）

| 阶段 | 模块 | 第一个失败测试建议 |
|---|---|---|
| **P0** | `parser.parse_url` | AC6: 非法 URL 抛 `URLParseError` |
| **P0** | `parser.output_path` | AC1: `parse_url(...) → output_path(...)` 等于 `out/octocat/Hello-World/issues/1.md` |
| **P1** | `errors` | 各异常类 `exit_code` 属性正确 |
| **P1** | `github.fetch` (Issue) | 用 `pytest-httpserver` mock `/repos/{o}/{r}/issues/{n}` 返回 fixture |
| **P1** | `converter.render` | 给定 fixture `IssueData`，断言输出字符串包含 frontmatter 各字段 |
| **P2** | `cli._load_url_list` | 含 `#` 注释 / 空行 / 行内注释的混合输入 |
| **P2** | `cli._dedup` | AC9: 重复 URL 仅保留首次 |
| **P2** | `github.fetch` (PR) | PR fixture，断言 `merged` 字段被填充 |
| **P3** | `github.fetch` (Discussion) | GraphQL mock |
| **P3** | `cli.run` | AC5: 批量模式 + `--continue-on-error` 部分失败 |

---

## 7. 开放问题

- **`fetch` 是否拆为 `fetch_issue` / `fetch_pull` / `fetch_discussion`？**
  当前选择单一 `fetch` 内部路由，理由是 CLI 编排层不需要关心类型差异。
  若未来 PR 需要 commit 列表，可能拆分。
- **`render` 是否接受 `template` 参数？**
  v1 不接受（YAGNI）。模板化列入 v2 路线图。
