# 修复摘要

## 修复的问题
CI appstore 发布规范预检要求 `.claude/README.md` 位于 `.claude/` 根目录，而 PR 将其放在了 `.claude/agents/` 子目录下，导致路径校验失败。

## 修改的文件
- `.claude/agents/README.md` → `.claude/README.md`: 使用 `git mv` 将 README 从 `.claude/agents/` 子目录提升到 `.claude/` 根目录，同时修正了内部的相对引用 `../CLAUDE.md` → `CLAUDE.md`（因文件层级变化）。

## 修复逻辑
CI 的 `eulerpublisher` 预检工具扫描 `.claude/` 目录下的 README 文件时，要求路径必须是 `.claude/README.md`（根层级），而非 `.claude/agents/README.md`（子层级）。PR 将原 `.agents/` 目录重命名为 `.claude/` 时，其中 `.agents/agents/README.md` 被移动为 `.claude/agents/README.md`，触发了路径校验失败。修复方案是将 README 移动到 CI 要求的正确位置 `.claude/README.md`。

## 潜在风险
- `.claude/agents/README.md` 变为 `.claude/README.md` 后，原文件已不存在于 `agents/` 子目录中。已检查 PR 变更范围内所有文件，无其他文件引用旧路径 `.claude/agents/README.md`，无风险。