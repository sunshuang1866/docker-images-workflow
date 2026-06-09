# 修复摘要

## 修复的问题
CI appstore 发布规范预检失败：`.claude/agents/README.md` 路径不符合规范，CI 期望该文件位于 `.claude/README.md`。

## 修改的文件
- `.claude/README.md`: 从 `.claude/agents/README.md` 移动至此，并更新了内部目录树和相对路径引用

## 修复逻辑
CI 的 appstore 发布规范检查器要求 `.claude/` 目录下的 README 文件直接位于 `.claude/READMD.md`，而非嵌套在 `agents/` 子目录下。这是 `.agents/` → `.claude/` 迁移过程中目录结构遗留问题。修复采用 `git mv` 将文件移动到 CI 期望的位置，并同步更新了：
1. 文件内的目录树结构图（添加 README.md 条目）
2. CLAUDE.md 的引用路径从 `../CLAUDE.md` 改为 `CLAUDE.md`（同级目录）

## 潜在风险
无。该 README 仅作为工具包说明文档，未被其他脚本或代码引用（grep 确认无其他文件引用 `agents/README.md` 路径）。