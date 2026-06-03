# issue2md 项目开发宪法
# Version: 1.0, Ratified: 2025-06-03

本文件定义了本项目不可动摇的核心开发原则。所有AI Agent在进行技术规划和代码实现时，必须无条件遵循。

---

## 第一条：简单性原则 (Simplicity First)
**核心：** 遵循Python语言的"简单优于复杂"（Zen of Python）哲学。绝不进行不必要的抽象，绝不引入非必需的依赖。
- **1.1 (YAGNI):** 只实现`spec.md`中明确要求的功能。
- **1.2 (标准库优先):** 必须优先使用Python标准库，例如Web服务使用`http.server`或`flask`而非过度复杂的框架。
- **1.3 (反过度工程):** 简单的函数和字典优于复杂的类和继承体系。"显式优于隐式，简单优于复杂"。

---

## 第二条：测试先行铁律 (Test-First Imperative) - 不可协商
**核心：** 所有新功能或Bug修复，都必须从编写一个（或多个）失败的测试开始。
- **2.1 (TDD循环):** 严格遵循"Red-Green-Refactor"循环。先写测试，观察失败，实现功能，重构优化。
- **2.2 (pytest优先):** 单元测试必须使用`pytest`框架，充分利用其参数化测试（parametrize）功能。
- **2.3 (拒绝过度Mock):** 优先编写集成测试，使用真实的依赖。仅在必要时使用`unittest.mock`。

---

## 第三条：明确性原则 (Clarity and Explicitness)
**核心：** 代码的首要目的是让人类易于理解。Python之禅："优美胜于丑陋，明了胜于晦涩"。
- **3.1 (异常处理):** **不可协商**：所有异常都必须被显式处理。异常传递时必须使用`raise ... from err`进行链式追踪。
- **3.2 (无全局变量):** 绝不允许使用全局变量来传递状态，所有依赖必须通过函数参数或类构造函数显式注入。
- **3.3 (类型注解):** 所有公共API必须提供类型注解（Type Hints），使用`mypy`进行静态类型检查。

---

## 第四条：Pythonic代码风格 (Pythonic Code Style)
**核心：** 遵循PEP 8代码风格指南和Python惯用法。
- **4.1 (命名规范):** 
  - 函数和变量使用`snake_case`
  - 类使用`PascalCase`
  - 常量使用`UPPER_SNAKE_CASE`
- **4.2 (列表推导):** 优先使用列表推导式而非`map`/`filter`，但要保持可读性。
- **4.3 (上下文管理器):** 资源管理必须使用`with`语句（上下文管理器）。
- **4.4 (数据类):** 简单的数据容器优先使用`@dataclass`而非普通类。

---

## 第五条：依赖管理原则 (Dependency Management)
**核心：** 保持依赖最小化，确保环境可重现。
- **5.1 (虚拟环境):** 必须使用虚拟环境（venv或pyenv）隔离项目依赖。
- **5.2 (依赖锁定):** 使用`pip freeze > requirements.txt`或`poetry.lock`锁定依赖版本。
- **5.3 (安全审计):** 定期使用`pip-audit`或`safety`检查依赖安全漏洞。

---

## 治理 (Governance)
本宪法具有最高优先级，其效力高于任何`CLAUDE.md`或单次会话中的指令。当出现原则冲突时，以"简单性"和"明确性"为最高准则。

---

## 附录：Python之禅（节选）
> Beautiful is better than ugly.<br>
> Explicit is better than implicit.<br>
> Simple is better than complex.<br>
> Complex is better than complicated.<br>
> Flat is better than nested.<br>
> Sparse is better than dense.<br>
> Readability counts.<br>
> Errors should never pass silently.<br>
> In the face of ambiguity, refuse the temptation to guess.
