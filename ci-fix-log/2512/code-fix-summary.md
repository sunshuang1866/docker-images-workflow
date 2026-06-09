# 修复摘要

## 修复的问题
CI appstore 发布规范预检失败：`.claude/agents/README.md` 路径不符合规范，期望路径为 `.claude/README.md`。

## 修改的文件
- `.claude/agents/README.md` → `.claude/README.md`: 将 README 从 `agents/` 子目录移动到 `.claude/` 根目录，并修正内部的相对路径引用 `../CLAUDE.md` → `./CLAUDE.md`

## 修复逻辑
CI appstore 预检脚本要求 `.claude/` 目录的 README 文件位于 `.claude/README.md`（根层级）。PR 将整个工具链从 `.agents/` 重命名为 `.claude/` 时，README 被放置在 `.claude/agents/README.md`（子目录层级），不符合 CI 路径规范。修复方案采用分析报告建议的方向 1（高置信度），通过 git mv 将 README 移动到正确的路径，并更新内部相对路径引用以适配新位置。

## 潜在风险
无