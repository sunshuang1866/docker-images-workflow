# 修复摘要

## 修复的问题
CI appstore 路径校验失败：`.claude/agents/README.md` 不在期望路径 `.claude/README.md`。

## 修改的文件
- `.claude/agents/README.md` → `.claude/README.md`: 将 README 文件从 `agents/` 子目录移动到 `.claude/` 根目录，并修正了内部相对引用 `../CLAUDE.md` → `CLAUDE.md`。

## 修复逻辑
CI 的 appstore 发布路径校验器（`eulerpublisher/update/container/app/update.py`）要求 `.claude/` 目录下的 README 文件位于 `.claude/README.md`（根层级），而非 `.claude/agents/README.md`（子目录内）。本次修复将 README 移至 CI 期望的正确位置，符合分析报告中置信度最高的方向 1。同时更新了 README 中对 CLAUDE.md 的引用，因为现在两个文件处于同一目录层级，不再需要 `../` 前缀。

## 潜在风险
无。README 内容本身未变，移至根层级后架构图仍然准确（README 作为顶层文件介绍子目录结构）。`.claude/agents/` 目录下其他 agent 定义文件不受影响。