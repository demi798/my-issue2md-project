# issue2md

将 GitHub Issues/PRs/Discussions 转换为 Markdown 文件

## 特性

- ✅ 支持 Issue、Pull Request 和 Discussion 三种资源类型
- ✅ 批量处理多个 URL
- ✅ 从文件读取 URL 列表
- ✅ 自定义输出目录
- ✅ 限制评论数量
- ✅ GitHub Token 支持（环境变量或 CLI 参数）
- ✅ 错误处理和继续处理
- ✅ 限流自动重试
- ✅ 完整的 Markdown 输出（YAML frontmatter + 正文）

## 安装

```bash
# 克隆仓库
git clone https://github.com/demi798/issue2md.git
cd issue2md

# 安装依赖
pip install -e .
```

## 快速开始

### 单个 Issue

```bash
issue2md https://github.com/octocat/Hello-World/issues/1
```

### 单个 Pull Request

```bash
issue2md https://github.com/owner/repo/pull/42
```

### 单个 Discussion

```bash
issue2md https://github.com/vercel/next.js/discussions/100
```

### 批量处理

```bash
# 处理多个 URL
issue2md https://github.com/owner/repo/issues/1 https://github.com/owner/repo/pull/42

# 从文件读取 URL
issue2md -f urls.txt
```

### 自定义输出目录

```bash
issue2md -o ./my-output https://github.com/owner/repo/issues/1
```

### 限制评论数量

```bash
# 只保留前 10 条评论
issue2md --max-comments 10 https://github.com/owner/repo/issues/1
```

### 使用 GitHub Token

```bash
# 通过 CLI 参数
issue2md --token ghp_abc123 https://github.com/owner/repo/issues/1

# 通过环境变量
export GITHUB_TOKEN=ghp_abc123
issue2md https://github.com/owner/repo/issues/1
```

### 错误处理

```bash
# 遇到错误继续处理
issue2md --continue-on-error https://github.com/owner/repo/issues/1 https://github.com/owner/repo/issues/2
```

## 输出格式

生成的 Markdown 文件包含：

1. **YAML Frontmatter**：
   - url: 原始 GitHub URL
   - type: 资源类型 (issue/pull/discussion)
   - owner: 仓库所有者
   - repo: 仓库名
   - number: 编号
   - title: 标题
   - author: 作者
   - created_at: 创建时间
   - updated_at: 更新时间
   - labels: 标签列表
   - comments_count: 评论总数
   - fetched_at: 抓取时间
   - PR 特有字段：draft, merged, mergeable
   - Discussion 特有字段：category, answer_chosen

2. **Markdown 正文**：
   - 标题（包含状态：[open]/[closed]/[merged]）
   - 主帖内容
   - 评论部分（按时间升序排列）

## 示例输出

```markdown
---
url: https://github.com/octocat/Hello-World/issues/1
type: issue
owner: octocat
repo: Hello-World
number: 1
title: Test Issue
author: octocat
created_at: 2023-01-02T03:04:05+00:00
updated_at: 2023-06-01T07:08:09+00:00
labels:
- bug
- frontend
comments_count: 2
fetched_at: 2026-06-05T10:30:45.123456+00:00
state: open
---

# Test Issue  [open]

This is a test issue body

---

## Comments (2)

### Comment 1 — @user1 · 2023-01-02 04:00:00 UTC

Comment 1 content

### Comment 2 — @user2 · 2023-01-02 05:00:00 UTC

Comment 2 content
```

## 开发

### 环境设置

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
make test

# 代码格式化
make format

# 类型检查
make typecheck

# 代码质量检查
make lint

# 依赖审计
make audit
```

### 构建命令

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

## 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 致谢

- [Python](https://www.python.org/) - 编程语言
- [GitHub API](https://docs.github.com/en/rest) - 数据源
- [pytest](https://docs.pytest.org/) - 测试框架
- [requests](https://docs.python-requests.org/) - HTTP 客户端

## 联系方式

- 项目主页：https://github.com/demi798/issue2md
- 作者：demi798