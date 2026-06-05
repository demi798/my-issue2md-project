# issue2md

将 GitHub Issues、Pull Requests 和 Discussions 转换为结构化的 Markdown 文件

![GitHub Actions](https://github.com/demi798/issue2md/workflows/CI/badge.svg)
![PyPI](https://img.shields.io/pypi/v/issue2md.svg)
![Python Version](https://img.shields.io/pypi/pyversions/issue2md.svg)
![License](https://img.shields.io/pypi/l/issue2md.svg)

## 📖 项目概述

`issue2md` 是一个轻量级的命令行工具，用于将 GitHub 上的 Issues、Pull Requests 和 Discussions 转换为完整的 Markdown 文件。生成的文件包含 YAML frontmatter 元数据和格式化的正文内容，便于本地存储、离线查看和文档归档。

## ✨ 核心特性

### 🎯 支持的 GitHub 资源类型
- ✅ **Issues** - 完整的问题跟踪
- ✅ **Pull Requests** - 代码审查和合并请求
- ✅ **Discussions** - 社区讨论（使用 GraphQL API）

### 🚀 功能特性
- **批量处理** - 一次处理多个 URL
- **文件输入** - 从文本文件读取 URL 列表
- **自定义输出** - 指定输出目录结构
- **评论限制** - 控制每条记录包含的评论数量
- **Token 支持** - 通过 CLI 参数或环境变量提供 GitHub Token
- **错误恢复** - 遇到错误时继续处理其他 URL
- **限流处理** - 自动检测并等待 GitHub API 限流
- **完整元数据** - 包含所有相关信息的 YAML frontmatter
- **格式化输出** - 专业的 Markdown 格式，包含状态标识

### 🛡️ 健壮性
- 自动重试机制处理 API 限流
- 详细的错误信息和退出码
- 完善的异常处理
- 输入验证和清理

## 📦 安装

### 通过 PyPI 安装（推荐）
```bash
pip install issue2md
```

### 从源码安装
```bash
# 克隆仓库
git clone https://github.com/demi798/issue2md.git
cd issue2md

# 安装依赖
pip install -e .
```

## 🚀 快速开始

### 基本用法

#### 单个 Issue
```bash
issue2md https://github.com/octocat/Hello-World/issues/1
```

#### 单个 Pull Request
```bash
issue2md https://github.com/owner/repo/pull/42
```

#### 单个 Discussion
```bash
issue2md https://github.com/vercel/next.js/discussions/100
```

### 批量处理

#### 多个 URL
```bash
issue2md https://github.com/owner/repo/issues/1 https://github.com/owner/repo/pull/42
```

#### 从文件读取
```bash
# urls.txt 内容：
# https://github.com/owner/repo/issues/1
# https://github.com/owner/repo/pull/42
# https://github.com/owner/repo/discussions/10

issue2md -f urls.txt
```

### 高级选项

#### 自定义输出目录
```bash
issue2md -o ./my-output https://github.com/owner/repo/issues/1
```

#### 限制评论数量
```bash
# 只保留前 10 条评论
issue2md --max-comments 10 https://github.com/owner/repo/issues/1
```

#### 使用 GitHub Token
```bash
# 通过 CLI 参数
issue2md --token ghp_abc123 https://github.com/owner/repo/issues/1

# 通过环境变量
export GITHUB_TOKEN=ghp_abc123
issue2md https://github.com/owner/repo/issues/1
```

#### 错误处理
```bash
# 遇到错误继续处理
issue2md --continue-on-error https://github.com/owner/repo/issues/1 https://github.com/owner/repo/issues/2
```

## 📋 输出格式

生成的 Markdown 文件包含两部分：

### 1. YAML Frontmatter（元数据）
```yaml
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
```

### 2. Markdown 正文
```markdown
# Test Issue  [open]

This is a test issue body

---

## Comments (2)

### Comment 1 — @user1 · 2023-01-02 04:00:00 UTC

Comment 1 content

### Comment 2 — @user2 · 2023-01-02 05:00:00 UTC

Comment 2 content
```

## 🏗️ 项目架构

```
issue2md/
├── issue2md/              # 主源代码包
│   ├── cli/              # 命令行接口
│   ├── core/             # 核心业务逻辑
│   │   ├── converter.py  # Markdown 转换
│   │   ├── parser.py     # URL 解析
│   │   └── github.py     # GitHub API 交互
│   ├── models/           # 数据模型
│   └── errors/          # 异常定义
├── tests/                # 测试代码
└── specs/                # 功能规格文档
```

### 核心模块

- **CLI 入口** (`cli/main.py`) - 处理命令行参数和主流程
- **URL 解析** (`core/parser.py`) - 解析 GitHub URL 为结构化引用
- **GitHub API 交互** (`core/github.py`) - 处理 API 请求、分页和错误处理
- **Markdown 转换** (`core/converter.py`) - 生成 YAML frontmatter 和 Markdown 正文
- **数据模型** (`models/`) - 使用 `dataclass` 定义 Issue、Discussion 等数据结构

## 🛠️ 开发指南

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

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

### 开发规范

- 遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范
- 运行 `make format` 确保代码格式化
- 运行 `make typecheck` 确保类型检查通过
- 编写测试用例，目标覆盖率 >80%

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Python](https://www.python.org/) - 编程语言
- [GitHub API](https://docs.github.com/en/rest) - 数据源
- [pytest](https://docs.pytest.org/) - 测试框架
- [requests](https://docs.python-requests.org/) - HTTP 客户端

## 📞 联系方式

- 项目主页：https://github.com/demi798/issue2md
- 作者：demi798


## 📜 变更日志

### v1.0.0 (2025-06-03)
- 初始版本发布
- 支持 Issue、Pull Request 和 Discussion
- 完整的 Markdown 输出格式
- 健壮的错误处理和限流机制