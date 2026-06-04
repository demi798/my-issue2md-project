# issue2md — 功能规格文档 (Specification)

> **Version:** 1.0
> **Status:** Draft
> **Last Updated:** 2026-06-04
> **Owner:** demi798 + Claude（共创）

---

## 0. 概述 (Overview)

### 0.1 一句话定义
`issue2md` 是一个命令行工具，用于将 GitHub Issue / Pull Request / Discussion 的 URL 转换为本地结构化的 Markdown 文件，专为自动化流水线场景设计。

### 0.2 目标用户与场景
- **主要场景**：CI/CD 流水线、批量归档脚本、知识库同步任务
- **次要场景**：开发者本地手动保存 Issue 用于离线阅读
- **非目标**：不做交互式 TUI、不做 Web UI、不做 GitHub Enterprise 的特殊适配（v1 不涉及）

### 0.3 设计原则
依照项目宪法，本工具坚持：
1. **简单性**：单一职责，只做"URL → 本地 .md 文件"这一件事
2. **明确性**：所有错误显式抛出并带语义化退出码，绝不静默吞掉异常
3. **可机器解析**：输出文件结构稳定、frontmatter 标准化，便于下游脚本消费
4. **流水线友好**：稳定性 > 输出美观；语义化退出码 > 友好提示

---

## 1. 功能需求 (Functional Requirements)

### 1.1 CLI 接口

#### 1.1.1 命令格式
```
issue2md [OPTIONS] [URL...]
```

#### 1.1.2 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `URL...` | 位置参数，可多个 | 否（与 `--from-file` 二选一） | — | 一个或多个 GitHub Issue/PR/Discussion URL |
| `-f, --from-file` | string | 否 | — | 从文件读取 URL 列表（每行一个，支持 `#` 注释与空行） |
| `-o, --output-dir` | path | 否 | `./out` | 输出根目录；子目录结构由工具自动生成 |
| `--force` | flag | 否 | false | 输出文件已存在时强制覆盖（**默认即覆盖**，此参数保留以备未来切换策略） |
| `--continue-on-error` | flag | 否 | false | 批量模式下遇到错误不中断，继续处理下一个 URL；最终汇总错误数 |
| `--max-comments` | int | 否 | `0`（=不限） | 限制每个 Issue/PR/Discussion 拉取的评论数量；`0` 表示全量 |
| `--token` | string | 否 | — | GitHub Token；未指定时读取 `GITHUB_TOKEN` 环境变量；都未设置走匿名 |
| `--help` | flag | 否 | — | 输出帮助信息 |
| `--version` | flag | 否 | — | 输出版本号 |

> **互斥约束**：`URL...` 与 `--from-file` 至少出现一个；同时出现时以位置参数为准并打印 warning。

#### 1.1.3 支持的 URL 形态
```
https://github.com/<owner>/<repo>/issues/<number>
https://github.com/<owner>/<repo>/pull/<number>
https://github.com/<owner>/<repo>/discussions/<number>
```

- 协议：仅 `https://`
- 域名：仅 `github.com`（v1 不支持 Enterprise）
- 末尾斜杠可选
- 不识别 `files/<n>`、`commits/<sha>`、`releases` 等其他资源类型，遇到时报错退出码 `1`

---

### 1.2 输出规范

#### 1.2.1 目录结构
所有输出文件落在 `<output-dir>` 下，按以下固定规则组织：

```
<output-dir>/
└── <owner>/
    └── <repo>/
        ├── issues/
        │   └── <number>.md
        ├── pulls/
        │   └── <number>.md
        └── discussions/
            └── <number>.md
```

- 路径中的 `owner`、`repo`、`number` 严格使用 URL 中出现的原始大小写
- 中间目录不存在时自动创建（含权限校验）

#### 1.2.2 文件命名冲突
- **默认覆盖**：直接重写目标文件，不提示
- v1 暂不实现 `--skip-existing` 等策略，保留扩展空间

#### 1.2.3 Markdown 文件结构

每个输出文件由两部分组成：**YAML frontmatter** + **正文**。

##### Frontmatter（必需字段）

```yaml
---
url: https://github.com/owner/repo/issues/123
type: issue            # issue | pull | discussion
owner: owner
repo: repo
number: 123
title: "Issue 标题原文"
state: open            # open | closed | merged（仅 PR 可能为 merged）
author: octocat
created_at: 2026-01-02T03:04:05Z
updated_at: 2026-06-01T07:08:09Z
labels: [bug, backend]
comments_count: 15
fetched_at: 2026-06-04T10:00:00Z   # 工具拉取时刻（UTC）
---
```

- Discussion 额外字段：`category: <name>`、`answer_chosen: true|false`
- PR 额外字段：`draft: bool`、`merged: bool`、`mergeable: bool|null`
- 所有时间字段使用 ISO 8601 UTC

##### 正文

```markdown
# <title>  [<state>]

<主帖正文（GitHub 返回的 markdown 原文）>

---

## Comments (<count>)

### Comment 1 — @<author> · <created_at>

<评论正文>

### Comment 2 — @<author> · <created_at>

<评论正文>
...
```

- 评论按 `created_at` **升序**排列
- 评论计数从 1 开始
- 评论正文之间使用 `###` 三级标题分隔
- PR 中的 review comments 与 issue comments 在 v1 中**合并按时间排序**输出（不区分来源）

---

### 1.3 鉴权策略

| 优先级 | 来源 |
|---|---|
| 1 | `--token` 命令行参数 |
| 2 | `GITHUB_TOKEN` 环境变量 |
| 3 | 匿名调用（限流 60 次/小时） |

- Token 格式校验：非空字符串，长度 ≥ 20；不符合时报错退出码 `4`
- Token 无权限（如访问私有仓库失败）→ 退出码 `4`
- 未提供 Token 且触发匿名限流 → 进入"限流处理"流程

---

### 1.4 错误处理与限流

#### 1.4.1 限流处理（403 / 429）
当收到响应且 `X-RateLimit-Remaining: 0`：
1. 读取 `X-RateLimit-Reset` 头（Unix 时间戳）
2. 计算需等待秒数（最多 600 秒，超过则报错退出）
3. stderr 打印 `[INFO] rate-limited, waiting Xs until reset...`
4. `sleep` 后**重试一次**
5. 仍失败 → 报错，退出码 `2`

#### 1.4.2 其他错误响应

| HTTP 状态 | 含义 | 退出码 |
|---|---|---|
| 401 | Token 无效 | 4 |
| 403 | 权限不足（非限流） | 4 |
| 404 | URL 不存在 / Discussion 未启用 | 2 |
| 5xx | GitHub 服务端错误 | 2 |
| 网络异常 | 连接失败 / DNS 失败 / 超时 | 2 |

#### 1.4.3 文件 IO 错误
- 目标目录不可写、磁盘满 → 退出码 `3`
- URL 格式错误、参数互斥冲突 → 退出码 `1`

---

### 1.5 退出码（语义化）

| Code | 含义 | 触发场景 |
|---|---|---|
| **0** | 成功 | 所有 URL 处理成功 |
| **1** | 参数错误 | URL 格式不合法、参数冲突、缺少必填项 |
| **2** | 网络 / API 错误 | 404、5xx、限流重试仍失败、网络中断 |
| **3** | 文件 IO 错误 | 无法创建目录、无法写入文件、磁盘满 |
| **4** | 鉴权错误 | Token 无效、无权限访问私有仓库 |

**批量模式特殊规则**（`--continue-on-error`）：
- 任一 URL 失败 → 继续处理后续
- 全部成功 → 退出码 `0`
- 部分失败 → 退出码取**已处理项中最严重的非 0 退出码**，并在 stderr 打印汇总：
  ```
  [SUMMARY] processed=10, succeeded=8, failed=2
  [FAILED] https://... → exit=2
  [FAILED] https://... → exit=4
  ```

---

### 1.6 批量与并发

- v1 **串行处理**多个 URL，不并发（避免触发 GitHub 二级限流）
- 单进程内同一 URL 自动去重（避免重复写入相同文件）
- `--from-file` 文件格式：
  - 每行一个 URL
  - 以 `#` 开头的行视为注释
  - 空白行忽略
  - 行内 `#` 之后的内容视为注释（`url # 备注` → 取 `url`）

---

## 2. 非功能需求 (Non-Functional Requirements)

### 2.1 性能
- 单个 Issue（含 100 条评论）端到端 < 5 秒（按 GitHub API 平均响应 200ms 估算）
- 无显式超时上限（依赖 `requests` 默认值）；后续可加 `--timeout`

### 2.2 可观测性
- 所有进度信息输出到 **stderr**（保持 stdout 干净，便于管道）
- 默认日志级别 `INFO`：每个 URL 处理前后各一行
- 失败时输出 `[ERROR]` 前缀 + 简明原因（不含 traceback，traceback 通过 `--verbose` 打开）

### 2.3 依赖约束
- **运行时依赖**：仅 `requests` + `PyYAML`
- **开发依赖**：`pytest`、`pytest-mock`、`mypy`、`ruff`、`black`
- 严禁引入 `PyGithub`、`httpx`、`rich` 等高阶库（违反宪法第一条）

### 2.4 Python 版本
- 支持 `>= 3.11`
- 允许使用 `|` 联合类型、`match-case`、`tomllib`、`Self` 等新特性

### 2.5 可移植性
- macOS / Linux 一等公民
- Windows 仅要求"能跑"，不保证路径分隔符完美（使用 `pathlib.Path` 即可）

---

## 3. 数据来源 (Data Sources)

### 3.1 Issue / PR
- **API**：GitHub REST API v3
- 端点：
  - `GET /repos/{owner}/{repo}/issues/{number}` （注意：PR 也可通过此端点获取，但 PR 推荐用 `/pulls/{number}`）
  - `GET /repos/{owner}/{repo}/issues/{number}/comments`
- 分页：`per_page=100`，通过 `Link` header 自动翻页

### 3.2 Discussion
- **API**：GitHub GraphQL API v4
- 原因：Discussion 不在 REST API 中暴露
- 查询字段：`title`、`body`、`author.login`、`createdAt`、`updatedAt`、`stateReason`、`labels`、`comments(first: 100, after: $cursor)` 递归翻页
- 仓库未启用 Discussion → GraphQL 返回 `NOT_FOUND` → 退出码 `2`

---

## 4. 边界与不做范围 (Out of Scope for v1)

明确**不实现**以下功能（遵循宪法第一条 YAGNI）：

- ❌ 图片附件下载（用户提到不下载）
- ❌ Reaction（👍 等）统计
- ❌ 跨 Issue 关联（referenced、duplicate 等）
- ❌ Git diff / commit 内容（PR 仅取主帖与评论）
- ❌ GitHub Enterprise 支持
- ❌ 增量同步（每次都全量重写）
- ❌ 并发拉取
- ❌ Web UI / TUI
- ❌ 自定义模板 / Jinja2 渲染

---

## 5. 验收标准 (Acceptance Criteria)

以下场景全部通过即可视为 v1 交付完成：

| # | 场景 | 预期 |
|---|---|---|
| AC1 | `issue2md https://github.com/octocat/Hello-World/issues/1` | 生成 `./out/octocat/Hello-World/issues/1.md`，含 frontmatter + 主帖 + 评论 |
| AC2 | 同上但未设 Token，连续执行 70 次 | 第 61 次起触发限流，等待后重试一次，仍失败则退出码 2 |
| AC3 | `issue2md https://github.com/x/y/pull/42` | 生成 `./out/x/y/pulls/42.md`，frontmatter 含 `state` 可能值 `merged` |
| AC4 | `issue2md https://github.com/vercel/next.js/discussions/100` | 通过 GraphQL 拉取，输出含 `category` 字段 |
| AC5 | `issue2md --from-file=urls.txt --continue-on-error` 文件含 3 个 URL，第 2 个 404 | 处理完 3 个，第 2 个跳过，最终退出码 2，stderr 打印 SUMMARY |
| AC6 | `issue2md https://invalid-url` | 退出码 1，stderr 提示 URL 格式错误 |
| AC7 | `issue2md <private-repo-url>` 未设 Token | 退出码 4，stderr 提示鉴权失败 |
| AC8 | 输出目录只读（`chmod 555 out/`） | 退出码 3 |
| AC9 | 同一 URL 在参数中重复出现 | 只处理一次 |
| AC10 | `--max-comments=5` 且 Issue 有 20 条评论 | 文件中只保留前 5 条评论，frontmatter `comments_count` 仍显示真实值 20 |

---

## 6. 测试策略 (Test Strategy)

遵循宪法第二条「测试先行」：

- **单元测试**：URL 解析、退出码映射、frontmatter 序列化、批量去重
- **集成测试**（推荐）：使用 `responses` 或 `pytest-httpserver` 模拟 GitHub API 响应
- **参数化测试**：覆盖 AC1–AC10 所有场景
- **不 Mock 内部函数**：只 Mock HTTP 层

---

## 7. 未来路线图 (Roadmap, not in v1)

仅供记录，**不影响 v1 决策**：

- v2：增量同步（基于 `updated_at` 判断是否需重新拉取）
- v2：图片下载 + 链接重写
- v2：GitHub Enterprise 支持
- v2：自定义输出模板
- v3：并发拉取 + Redis 限流共享池

---

## 8. 开放问题 (Open Questions)

> 这些问题不阻塞 v1 实现，但值得记录：

1. **Review comments 与 Issue comments 是否需要分别标注？**（v1 选择合并按时间排序，未来可加 `--separate-review-comments`）
2. **PR 的 commit 列表是否要附在文末？**（v1 不做）
3. **是否需要 `--dry-run` 模式？**（v1 不做，可在 v1.1 加）

---

**本规格文档结束。**

> 下一步建议：用户审阅后，由 AI 起草 `src/issue2md/` 的模块拆分与第一个失败的 pytest 用例。
