# 修复摘要

## 修复的问题
CI appstore 发布规范预检失败：`.claude/agents/README.md` 路径不符合预期，要求 README.md 位于 `.claude/README.md`。

## 修改的文件
- `.claude/agents/README.md` → `.claude/README.md`: 将 README.md 从 `agents/` 子目录移到 `.claude/` 根目录，使其符合 CI 路径校验规则

## 修复逻辑
PR #2512 在将目录从 `.agents/` 重命名为 `.claude/` 时，README.md 被放在 `.claude/agents/` 子目录下，但 CI 的 appstore 发布规范检查期望 README.md 在 `.claude/` 根目录。将文件向上提一级即可满足校验。同时修正了文件内部的相对路径引用：`../CLAUDE.md` → `CLAUDE.md`。

## 潜在风险
无