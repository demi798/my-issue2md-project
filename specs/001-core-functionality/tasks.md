# issue2md 任务列表

> **Version:** 1.0
> **Created:** 2026-06-04
> **Based on:** plan.md, spec.md
> **Status:** Ready for AI Execution

---

## 符号说明

| 符号 | 含义 |
|------|------|
| `[P]` | 可并行执行（无前置依赖） |
| `T-` | 测试任务 |
| `I-` | 实现任务 |
| `→` | 依赖关系 |

---

## Phase 1: Foundation (数据结构定义)

### 1.1 项目基础设施

#### [P] T-F1.1: 创建项目基础目录结构
- 创建目录：`issue2md/`, `issue2md/cli/`, `issue2md/core/`, `issue2md/models/`, `issue2md/errors/`
- 创建目录：`tests/unit/`, `tests/integration/`
- 创建所有 `__init__.py` 文件

#### [P] I-F1.1: 创建 pyproject.toml
- 文件：`pyproject.toml`
- 内容：项目元数据、运行时依赖（requests, pyyaml）、开发依赖配置

#### [P] I-F1.2: 创建 Makefile
- 文件：`Makefile`
- 内容：all, test, install, format, typecheck, lint, audit, clean 目标

#### [P] I-F1.3: 创建 pytest 配置
- 文件：`tests/conftest.py`
- 内容：pytest fixtures 定义

### 1.2 数据模型（models/）

#### [P] T-F2.1: 测试 ResourceType 枚举
- 文件：`tests/unit/test_resource.py`
- 测试：ISSUE/PULL/DISCUSSION 值正确，类型为 str

#### [P] T-F2.2: 测试 ResourceRef dataclass
- 文件：`tests/unit/test_resource.py`
- 测试：frozen=True 不可变，url 属性返回正确格式

#### [P] T-F2.3: 测试 ResourceRef 可比较性
- 文件：`tests/unit/test_resource.py`
- 测试：两个相同 ResourceRef 相等

#### I-F2.1: 实现 ResourceRef 和 ResourceType
- 文件：`issue2md/models/resource.py`
- 内容：ResourceType 枚举，ResourceRef dataclass（frozen=True），url 属性

#### [P] T-F2.4: 测试 Label dataclass
- 文件：`tests/unit/test_issue.py`
- 测试：name 必填，color 可选，frozen=True

#### [P] T-F2.5: 测试 Comment dataclass
- 文件：`tests/unit/test_issue.py`
- 测试：author, body, created_at 必填，frozen=True

#### [P] T-F2.6: 测试 IssueData dataclass
- 文件：`tests/unit/test_issue.py`
- 测试：基本字段必填，PR 专用字段默认 None
- 测试：comments_count 属性返回正确值
- 测试：type 属性根据 ref.type 返回 "issue" 或 "pull"

#### I-F2.2: 实现 IssueData 相关数据类
- 文件：`issue2md/models/issue.py`
- 内容：Label, Comment, IssueData dataclass（frozen=True），comments_count 和 type 属性

#### [P] T-F2.7: 测试 DiscussionData dataclass
- 文件：`tests/unit/test_discussion.py`
- 测试：基本字段必填，answer_chosen 默认 False
- 测试：comments_count 属性返回正确值
- 测试：type 属性返回 "discussion"

#### I-F2.3: 实现 DiscussionData
- 文件：`issue2md/models/discussion.py`
- 内容：DiscussionData dataclass（frozen=True），comments_count 和 type 属性

### 1.3 异常定义（errors/）

#### [P] T-F3.1: 测试 Issue2mdError 基类
- 文件：`tests/unit/test_errors.py`
- 测试：exit_code 默认 1，message 属性可访问

#### [P] T-F3.2: 测试各子类 exit_code
- 文件：`tests/unit/test_errors.py`
- 测试：URLParseError=1, AuthError=4, RateLimitError=2, GithubAPIError=2, FileIOError=3

#### [P] T-F3.3: 测试异常 __str__ 格式
- 文件：`tests/unit/test_errors.py`
- 测试：字符串格式为 "[ERROR] {message}"

#### I-F3.1: 实现异常类
- 文件：`issue2md/errors/exceptions.py`
- 内容：Issue2mdError 基类 + 5 个子类

### 1.4 模块导出

#### [P] I-F4.1: 创建 models/__init__.py
- 文件：`issue2md/models/__init__.py`
- 内容：导出所有数据类

#### [P] I-F4.2: 创建 errors/__init__.py
- 文件：`issue2md/errors/__init__.py`
- 内容：导出所有异常类

---

## Phase 2: GitHub Fetcher (API交互逻辑，TDD)

### 2.1 URL Parser

#### [P] T-G1.1: 测试 parse_url 识别合法 Issue URL
- 文件：`tests/unit/test_parser.py`
- 测试：https://github.com/octocat/Hello-World/issues/1 → 正确 ResourceRef

#### [P] T-G1.2: 测试 parse_url 识别合法 PR URL
- 文件：`tests/unit/test_parser.py`
- 测试：https://github.com/owner/repo/pull/42 → 正确 ResourceRef

#### [P] T-G1.3: 测试 parse_url 识别合法 Discussion URL
- 文件：`tests/unit/test_parser.py`
- 测试：https://github.com/vercel/next.js/discussions/100 → 正确 ResourceRef

#### [P] T-G1.4: 测试 parse_url 处理末尾斜杠
- 文件：`tests/unit/test_parser.py`
- 测试：末尾带 / 的 URL 正确解析

#### [P] T-G1.5: 测试 parse_url 非法 URL 抛 URLParseError
- 文件：`tests/unit/test_parser.py`
- 测试：非 https、非 github.com、非目标资源、number 非数字 → 抛 URLParseError

#### I-G1.1: 实现 parse_url 函数
- 文件：`issue2md/core/parser.py`
- 内容：URL 解析逻辑，抛 URLParseError

#### [P] T-G1.6: 测试 output_path 正确拼接路径
- 文件：`tests/unit/test_parser.py`
- 测试：ResourceRef + root → 正确 Path

#### I-G1.2: 实现 output_path 函数
- 文件：`issue2md/core/parser.py`
- 内容：路径拼接逻辑

#### [P] I-G1.3: 创建 core/__init__.py
- 文件：`issue2md/core/__init__.py`
- 内容：导出 parse_url, output_path

### 2.2 Token Validation

#### [P] T-G2.1: 测试 validate_token 空字符串抛 AuthError
- 文件：`tests/unit/test_github.py`
- 测试：空字符串 → AuthError

#### [P] T-G2.2: 测试 validate_token 短字符串抛 AuthError
- 文件：`tests/unit/test_github.py`
- 测试：长度 < 20 → AuthError

#### [P] T-G2.3: 测试 validate_token 合法 Token 不抛异常
- 文件：`tests/unit/test_github.py`
- 测试：长度 >= 20 的合法 Token 不抛异常

#### I-G2.1: 实现 validate_token 函数
- 文件：`issue2md/core/github.py`
- 内容：Token 格式校验逻辑

### 2.3 GitHub API - Issue Fetch

#### [P] T-G3.1: 测试 _handle_response 401 → AuthError
- 文件：`tests/unit/test_github.py`
- 测试：mock Response status=401 → AuthError

#### [P] T-G3.2: 测试 _handle_response 403 → AuthError
- 文件：`tests/unit/test_github.py`
- 测试：mock Response status=403 → AuthError

#### [P] T-G3.3: 测试 _handle_response 404 → GithubAPIError
- 文件：`tests/unit/test_github.py`
- 测试：mock Response status=404 → GithubAPIError

#### [P] T-G3.4: 测试 _handle_response 5xx → GithubAPIError
- 文件：`tests/unit/test_github.py`
- 测试：mock Response status=500 → GithubAPIError

#### [P] T-G3.5: 测试 _handle_response 限流检测
- 文件：`tests/unit/test_github.py`
- 测试：X-RateLimit-Remaining=0 → 返回重试标记

#### [P] T-G3.6: 测试 _handle_response 限流等待时间过长
- 文件：`tests/unit/test_github.py`
- 测试：reset - now > 600 秒 → RateLimitError

#### I-G3.1: 实现 _handle_response 函数
- 文件：`issue2md/core/github.py`
- 内容：HTTP 响应处理逻辑，限流检测

#### [P] T-G4.1: 集成测试：fetch Issue 成功（单页评论）
- 文件：`tests/integration/test_github_issue.py`
- 测试：使用 pytest-httpserver mock GitHub API，返回 IssueData

#### [P] T-G4.2: 集成测试：fetch Issue 成功（多页评论）
- 文件：`tests/integration/test_github_issue.py`
- 测试：模拟 Link header 分页，合并所有评论

#### [P] T-G4.3: 集成测试：fetch Issue 评论排序
- 文件：`tests/integration/test_github_issue.py`
- 测试：评论按 created_at 升序排列

#### [P] T-G4.4: 集成测试：fetch Issue 网络错误
- 文件：`tests/integration/test_github_issue.py`
- 测试：requests 异常 → GithubAPIError

#### [P] T-G4.5: 集成测试：fetch Issue 限流重试
- 文件：`tests/integration/test_github_issue.py`
- 测试：X-RateLimit-Remaining=0 → 等待后重试一次

#### I-G4.1: 实现 fetch 函数（Issue 分支）
- 文件：`issue2md/core/github.py`
- 内容：REST API 调用，评论分页，返回 IssueData

### 2.4 GitHub API - PR Fetch

#### [P] T-G5.1: 集成测试：fetch PR 成功
- 文件：`tests/integration/test_github_pull.py`
- 测试：mock PR API，返回 IssueData（填充 PR 专用字段）

#### [P] T-G5.2: 集成测试：fetch PR 字段完整性
- 文件：`tests/integration/test_github_pull.py`
- 测试：draft, merged, mergeable 字段正确填充

#### [P] T-G5.3: 集成测试：fetch PR state 为 merged
- 文件：`tests/integration/test_github_pull.py`
- 测试：merged=True 时 state 为 "merged"

#### I-G5.1: 扩展 fetch 函数（PR 分支）
- 文件：`issue2md/core/github.py`
- 内容：检测 pull_request 字段，调用 PR API，填充 PR 专用字段

### 2.5 GitHub API - Discussion Fetch

#### [P] T-G6.1: 集成测试：fetch Discussion 成功
- 文件：`tests/integration/test_github_discussion.py`
- 测试：mock GraphQL API，返回 DiscussionData

#### [P] T-G6.2: 集成测试：fetch Discussion category 字段
- 文件：`tests/integration/test_github_discussion.py`
- 测试：category 字段正确填充

#### [P] T-G6.3: 集成测试：fetch Discussion 递归翻页
- 文件：`tests/integration/test_github_discussion.py`
- 测试：使用 cursor 递归拉取所有评论

#### [P] T-G6.4: 集成测试：fetch Discussion NOT_FOUND
- 文件：`tests/integration/test_github_discussion.py`
- 测试：GraphQL 返回 NOT_FOUND → GithubAPIError

#### I-G6.1: 实现 fetch 函数（Discussion 分支）
- 文件：`issue2md/core/github.py`
- 内容：GraphQL 查询，递归翻页，返回 DiscussionData

#### [P] I-G6.2: 创建 GraphQL 查询模块（可选）
- 文件：`issue2md/core/queries.py` 或内联在 github.py
- 内容：GraphQL 查询字符串模板

#### [P] I-G6.3: 更新 core/__init__.py
- 文件：`issue2md/core/__init__.py`
- 内容：导出 fetch, validate_token

---

## Phase 3: Markdown Converter (转换逻辑，TDD)

### 3.1 Frontmatter 生成

#### [P] T-C1.1: 测试 render_frontmatter IssueData
- 文件：`tests/unit/test_converter.py`
- 测试：IssueData → 正确 YAML frontmatter

#### [P] T-C1.2: 测试 render_frontmatter PR 专用字段
- 文件：`tests/unit/test_converter.py`
- 测试：PR 的 draft, merged, mergeable 字段包含在内

#### [P] T-C1.3: 测试 render_frontmatter DiscussionData
- 文件：`tests/unit/test_converter.py`
- 测试：DiscussionData 包含 category, answer_chosen 字段

#### [P] T-C1.4: 测试 render_frontmatter 时间格式 ISO 8601
- 文件：`tests/unit/test_converter.py`
- 测试：created_at, updated_at, fetched_at 格式正确

#### [P] T-C1.5: 测试 render_frontmatter YAML 转义
- 文件：`tests/unit/test_converter.py`
- 测试：title 中的引号正确转义

#### I-C1.1: 实现 render_frontmatter 函数
- 文件：`issue2md/core/converter.py`
- 内容：数据 → YAML frontmatter 字符串

### 3.2 Body 生成

#### [P] T-C2.1: 测试 render_body 标题部分
- 文件：`tests/unit/test_converter.py`
- 测试：输出包含 `# <title>  [<state>]`

#### [P] T-C2.2: 测试 render_body 主帖内容
- 文件：`tests/unit/test_converter.py`
- 测试：主帖 body 原文输出

#### [P] T-C2.3: 测试 render_body 零评论
- 文件：`tests/unit/test_converter.py`
- 测试：输出 `## Comments (0)` 占位

#### [P] T-C2.4: 测试 render_body 单评论
- 文件：`tests/unit/test_converter.py`
- 测试：输出 `### Comment 1 — @author · created_at` 和评论内容

#### [P] T-C2.5: 测试 render_body 多评论排序
- 文件：`tests/unit/test_converter.py`
- 测试：评论按 created_at 升序，编号从 1 开始

#### [P] T-C2.6: 测试 render_body max_comments 截断
- 文件：`tests/unit/test_converter.py`
- 测试：max_comments=N 时只输出前 N 条评论

#### [P] T-C2.7: 测试 render_body max_comments=0 全量
- 文件：`tests/unit/test_converter.py`
- 测试：max_comments=0 时输出所有评论

#### I-C2.1: 实现 render_body 函数
- 文件：`issue2md/core/converter.py`
- 内容：数据 → Markdown 正文字符串

### 3.3 完整渲染

#### [P] T-C3.1: 测试 render 函数 IssueData
- 文件：`tests/unit/test_converter.py`
- 测试：frontmatter + body 完整输出

#### [P] T-C3.2: 测试 render 函数 DiscussionData
- 文件：`tests/unit/test_converter.py`
- 测试：frontmatter + body 完整输出

#### [P] T-C3.3: 测试 render 函数 max_comments 传递
- 文件：`tests/unit/test_converter.py`
- 测试：max_comments 参数正确传递到 render_body

#### [P] T-C3.4: 测试 render 函数 fetched_at 时间
- 文件：`tests/unit/test_converter.py`
- 测试：fetched_at 使用当前 UTC 时间

#### I-C3.1: 实现 render 函数
- 文件：`issue2md/core/converter.py`
- 内容：调用 render_frontmatter + render_body，组合输出

#### [P] I-C3.2: 更新 core/__init__.py
- 文件：`issue2md/core/__init__.py`
- 内容：导出 render

---

## Phase 4: CLI Assembly (命令行入口集成)

### 4.1 CLI 参数解析

#### [P] T-A1.1: 测试 parse_args 位置参数 URLs
- 文件：`tests/unit/test_cli_args.py`
- 测试：`url1 url2` → urls=["url1", "url2"]

#### [P] T-A1.2: 测试 parse_args --from-file
- 文件：`tests/unit/test_cli_args.py`
- 测试：`--from-file=urls.txt` → 正确 Path

#### [P] T-A1.3: 测试 parse_args --output-dir 默认值
- 文件：`tests/unit/test_cli_args.py`
- 测试：未指定时默认 Path("out")

#### [P] T-A1.4: 测试 parse_args --max-comments
- 文件：`tests/unit/test_cli_args.py`
- 测试：`--max-comments=5` → max_comments=5

#### [P] T-A1.5: 测试 parse_args --token
- 文件：`tests/unit/test_cli_args.py`
- 测试：`--token=abc123` → token="abc123"

#### [P] T-A1.6: 测试 parse_args --continue-on-error
- 文件：`tests/unit/test_cli_args.py`
- 测试：flag 正确设置为 True

#### [P] T-A1.7: 测试 parse_args --verbose
- 文件：`tests/unit/test_cli_args.py`
- 测试：flag 正确设置为 True

#### I-A1.1: 实现 parse_args 函数
- 文件：`issue2md/cli/args.py` 或内联在 __main__.py
- 内容：argparse 配置，所有 CLI 参数

#### [P] I-A1.2: 创建 cli/__init__.py
- 文件：`issue2md/cli/__init__.py`
- 内容：导出 parse_args（如独立文件）

### 4.2 URL 列表加载

#### [P] T-A2.1: 测试 _load_url_list 基本读取
- 文件：`tests/unit/test_cli.py`
- 测试：每行一个 URL → 列表

#### [P] T-A2.2: 测试 _load_url_list 跳过空行
- 文件：`tests/unit/test_cli.py`
- 测试：空行被忽略

#### [P] T-A2.3: 测试 _load_url_list 跳过 # 注释行
- 文件：`tests/unit/test_cli.py`
- 测试：以 # 开头的行被忽略

#### [P] T-A2.4: 测试 _load_url_list 行内 # 注释
- 文件：`tests/unit/test_cli.py`
- 测试：`url # comment` → 提取 `url`

#### [P] T-A2.5: 测试 _load_url_list 文件不存在抛 FileIOError
- 文件：`tests/unit/test_cli.py`
- 测试：文件不存在 → FileIOError

#### I-A2.1: 实现 _load_url_list 函数
- 文件：`issue2md/cli/main.py`
- 内容：文件读取，行过滤

### 4.3 URL 去重

#### [P] T-A3.1: 测试 _dedup 基本去重
- 文件：`tests/unit/test_cli.py`
- 测试：重复 URL 只保留首次

#### [P] T-A3.2: 测试 _dedup 保持顺序
- 文件：`tests/unit/test_cli.py`
- 测试：首次出现的顺序保持

#### I-A3.1: 实现 _dedup 函数
- 文件：`issue2md/cli/main.py`
- 内容：URL 去重逻辑

### 4.4 单 URL 处理

#### [P] T-A4.1: 测试 _process_url 成功流程
- 文件：`tests/unit/test_cli.py`
- 测试：parse_url → fetch → render → write_file → 成功

#### [P] T-A4.2: 测试 _process_url 解析失败
- 文件：`tests/unit/test_cli.py`
- 测试：URLParseError → 抛出

#### [P] T-A4.3: 测试 _process_url API 失败
- 文件：`tests/unit/test_cli.py`
- 测试：GithubAPIError → 抛出

#### [P] T-A4.4: 测试 _process_url 写入失败
- 文件：`tests/unit/test_cli.py`
- 测试：FileIOError → 抛出

#### I-A4.1: 实现 _process_url 函数
- 文件：`issue2md/cli/main.py`
- 内容：编排逻辑，调用 parser/github/converter

### 4.5 文件写入

#### [P] T-A5.1: 测试 _write_file 成功
- 文件：`tests/unit/test_cli.py`
- 测试：创建目录，写入文件

#### [P] T-A5.2: 测试 _write_file 目录不可写
- 文件：`tests/unit/test_cli.py`
- 测试：权限不足 → FileIOError

#### [P] T-A5.3: 测试 _write_file 磁盘满
- 文件：`tests/unit/test_cli.py`
- 测试：OSError → FileIOError

#### I-A5.1: 实现 _write_file 函数
- 文件：`issue2md/cli/main.py`
- 内容：路径创建，文件写入

### 4.6 主流程编排

#### [P] T-A6.1: 集成测试：main 单个 Issue 成功
- 文件：`tests/integration/test_cli.py`
- 测试：AC1 场景，生成正确 .md 文件

#### [P] T-A6.2: 集成测试：main 单个 PR 成功
- 文件：`tests/integration/test_cli.py`
- 测试：AC3 场景，PR 正确处理

#### [P] T-A6.3: 集成测试：main 单个 Discussion 成功
- 文件：`tests/integration/test_cli.py`
- 测试：AC4 场景，category 字段正确

#### [P] T-A6.4: 集成测试：main 非法 URL 退出码 1
- 文件：`tests/integration/test_cli.py`
- 测试：AC6 场景，exit_code=1

#### [P] T-A6.5: 集成测试：main 私有仓库无 Token 退出码 4
- 文件：`tests/integration/test_cli.py`
- 测试：AC7 场景，exit_code=4

#### [P] T-A6.6: 集成测试：main 只读目录退出码 3
- 文件：`tests/integration/test_cli.py`
- 测试：AC8 场景，exit_code=3

#### I-A6.1: 实现 main 函数（基本流程）
- 文件：`issue2md/cli/main.py`
- 内容：参数解析，URL 收集，循环处理

### 4.7 批量处理

#### [P] T-A7.1: 测试 _run_batch 成功全部
- 文件：`tests/unit/test_cli.py`
- 测试：多个 URL 全部成功 → exit_code=0

#### [P] T-A7.2: 测试 _run_batch continue-on-error
- 文件：`tests/unit/test_cli.py`
- 测试：部分失败继续处理 → exit_code=最严重错误码

#### [P] T-A7.3: 测试 _run_batch 错误汇总
- 文件：`tests/unit/test_cli.py`
- 测试：stderr 输出 SUMMARY 和 FAILED 列表

#### [P] T-A7.4: 测试 _run_batch URL 去重
- 文件：`tests/unit/test_cli.py`
- 测试：AC9 场景，重复 URL 只处理一次

#### I-A7.1: 实现 _run_batch 函数
- 文件：`issue2md/cli/main.py`
- 内容：批量处理逻辑，错误汇总

#### [P] I-A7.2: 更新 main 函数集成批量逻辑
- 文件：`issue2md/cli/main.py`
- 内容：集成 _run_batch

### 4.8 CLI 入口

#### [P] T-A8.1: 测试 __main__.py 可执行
- 文件：`tests/integration/test_cli.py`
- 测试：`python -m issue2md` 可运行

#### [P] T-A8.2: 集成测试：批量 + continue-on-error
- 文件：`tests/integration/test_cli.py`
- 测试：AC5 场景，3 个 URL 第 2 个 404

#### [P] T-A8.3: 集成测试：max-comments 截断
- 文件：`tests/integration/test_cli.py`
- 测试：AC10 场景，frontmatter 显示真实计数

#### I-A8.1: 实现 __main__.py
- 文件：`issue2md/__main__.py`
- 内容：CLI 入口，调用 main，sys.exit

### 4.9 Token 环境变量

#### [P] T-A9.1: 测试 Token 优先级
- 文件：`tests/unit/test_cli.py`
- 测试：CLI 参数 > 环境变量 > None

#### I-A9.1: 更新 main 函数处理 GITHUB_TOKEN
- 文件：`issue2md/cli/main.py`
- 内容：读取环境变量，优先级处理

### 4.10 包导出

#### [P] I-A10.1: 创建 issue2md/__init__.py
- 文件：`issue2md/__init__.py`
- 内容：导出所有公共 API

---

## Phase 5: 验收与质量

### 5.1 AC 场景全覆盖

#### [P] T-V1.1: 验收测试 AC1（Issue 单个）
- 文件：`tests/integration/test_acceptance.py`
- 测试：完整端到端场景

#### [P] T-V1.2: 验收测试 AC2（限流重试）
- 文件：`tests/integration/test_acceptance.py`
- 测试：模拟限流场景

#### [P] T-V1.3: 验收测试 AC3（PR 单个）
- 文件：`tests/integration/test_acceptance.py`
- 测试：PR 端到端场景

#### [P] T-V1.4: 验收测试 AC4（Discussion）
- 文件：`tests/integration/test_acceptance.py`
- 测试：Discussion 端到端场景

#### [P] T-V1.5: 验收测试 AC5（批量 + 错误继续）
- 文件：`tests/integration/test_acceptance.py`
- 测试：批量场景

#### [P] T-V1.6: 验收测试 AC6（非法 URL）
- 文件：`tests/integration/test_acceptance.py`
- 测试：参数错误场景

#### [P] T-V1.7: 验收测试 AC7（鉴权失败）
- 文件：`tests/integration/test_acceptance.py`
- 测试：私有仓库场景

#### [P] T-V1.8: 验收测试 AC8（IO 错误）
- 文件：`tests/integration/test_acceptance.py`
- 测试：权限问题场景

#### [P] T-V1.9: 验收测试 AC9（去重）
- 文件：`tests/integration/test_acceptance.py`
- 测试：重复 URL 场景

#### [P] T-V1.10: 验收测试 AC10（评论截断）
- 文件：`tests/integration/test_acceptance.py`
- 测试：max-comments 场景

### 5.2 类型检查

#### [P] I-V2.1: 运行 mypy 检查
- 命令：`mypy issue2md`
- 确保：所有类型注解正确，无 mypy 错误

### 5.3 代码格式化

#### [P] I-V3.1: 运行 black 格式化
- 命令：`black issue2md tests`

#### [P] I-V3.2: 运行 isort 导入排序
- 命令：`isort issue2md tests`

### 5.4 代码质量

#### [P] I-V4.1: 运行 ruff 检查
- 命令：`ruff check issue2md tests`

### 5.5 测试覆盖率

#### [P] I-V5.1: 运行 pytest 覆盖率
- 命令：`pytest tests/ --cov=issue2md --cov-report=term-missing`
- 确保：覆盖率 > 80%

### 5.6 依赖审计

#### [P] I-V6.1: 运行 pip-audit
- 命令：`pip-audit`
- 确保：无安全漏洞

---

## Phase 6: 文档与发布

### 6.1 项目文档

#### [P] I-D1.1: 创建 README.md
- 文件：`README.md`
- 内容：项目介绍、安装、使用、示例

#### [P] I-D1.2: 创建 LICENSE
- 文件：`LICENSE`
- 内容：开源协议（如 MIT）

#### [P] I-D1.3: 更新 .gitignore
- 文件：`.gitignore`
- 内容：Python 标准忽略项

### 6.2 Makefile 验证

#### [P] I-D2.1: 验证 Makefile 所有目标
- 测试：make all, make test, make install, make format, make typecheck, make lint, make audit, make clean

---

## 总结

- **总任务数**: 100+
- **测试任务**: ~50
- **实现任务**: ~50
- **可并行任务**: 标记 [P]
- **TDD 严格遵循**: 每个实现任务前有对应测试任务

执行顺序建议：
1. 逐阶段执行（Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6）
2. 同阶段内按依赖顺序执行
3. 标记 [P] 的任务可并行执行