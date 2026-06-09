# 修复摘要

## 修复的问题
CI appstore 发布规范检查要求 `.claude/` 工具目录的 README 文件位于根层级 `.claude/README.md`，而非嵌套在 `agents/` 子目录下的 `.claude/agents/README.md`。

## 修改的文件
- `.claude/README.md`: 新建，包含工具包完整说明文档（从 `.claude/agents/README.md` 迁移内容，并更新架构图中 README 自身路径及 CLAUDE.md 引用路径）
- `.claude/agents/README.md`: 清空原有内容，替换为简短索引说明，指向 `../README.md` 和 `../CLAUDE.md`

## 修复逻辑
CI 的 appstore 发布规范预检规则对 `.claude/` 工具目录下的 README 路径有严格校验：README 必须直接位于 `.claude/` 根下（即 `.claude/README.md`），不允许嵌套在 `agents/` 等子目录中。本次修复将 README 内容从 `.claude/agents/README.md` 迁移到 `.claude/README.md`，使其符合路径规范要求，同时将原文件改为简短索引，避免创建无内容的空文件。

## 潜在风险
无。迁移后的 `.claude/README.md` 保持了原文档的完整性和引用正确性（架构图路径和 CLAUDE.md 引用均已更新为对应的相对路径）。