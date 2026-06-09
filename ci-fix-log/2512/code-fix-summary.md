# 修复摘要

## 修复的问题
CI appstore 预检失败：`.claude/agents/README.md` 路径不符合规范，期望位置为 `.claude/README.md`。同时修复 Dockerfile 中 git 浅克隆与 commit hash checkout 的不兼容问题（预防性修复）。

## 修改的文件
- `.claude/README.md`: 新建文件，将工具包 README 从 `.claude/agents/` 子目录提升到 `.claude/` 根层级，并修正 `CLAUDE.md` 的相对引用路径（`../CLAUDE.md` → `CLAUDE.md`）
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 移除 `git clone` 的 `--depth 1 --shallow-submodules` 参数，移除 `git checkout` 的 `2>/dev/null || true` 错误掩盖，移除 `git submodule update` 的 `--depth 1` 参数

## 修复逻辑
1. **路径修正（高置信度，直接原因）**: CI 预检规则要求 `.claude/` 工具目录的 README 位于 `.claude/README.md`（根层级），但 PR 将其放在了 `.claude/agents/README.md`（子目录）。修复方式是将 README 文件创建在正确路径 `.claude/README.md`。同时修正了内部引用：从 `agents/` 提升到 `.claude/` 后，`CLAUDE.md` 成为同级文件，引用从 `../CLAUDE.md` 改为 `CLAUDE.md`。脚本引用 `python3 .claude/run_workflow.py` 等是相对于仓库根的，无需修改。

2. **Dockerfile git 克隆修复（中置信度，预防性）**: `git clone --depth 1` 仅拉取最新 commit，当 `git checkout ${VERSION}` 尝试切换到指定 commit hash (`22fca04`) 时可能无法找到该 commit。移除 `--depth 1` 进行完整克隆可确保任意 commit hash 均可被检出。同时移除 checkout 的 `|| true` 错误掩盖，确保构建在无法检出指定版本时正确失败。移除子模块更新的 `--depth 1` 确保子模块也能获取到正确的 commit。

## 潜在风险
- `.claude/agents/README.md` 原文件保留未删除，两个位置存在内容几乎相同的 README 文件。未来可能需要清理 `agents/` 子目录下的 README。当前保留不会导致 CI 再次失败（因 CI 只检查 `.claude/README.md` 是否存在）。
- Dockerfile 改为完整 git 克隆会增加构建时间和网络流量，但 3fs 仓库规模较小，影响可接受。