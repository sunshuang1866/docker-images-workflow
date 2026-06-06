# 修复摘要

## 修复的问题
修复 3FS Dockerfile 中 `git clone --recurse-submodules --shallow-submodules` 导致子模块在 checkout 后处于不一致状态，进而引发 cmake 构建失败的问题。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 从 `git clone` 命令中移除 `--recurse-submodules` 和 `--shallow-submodules` 参数，并移除 `git submodule update` 的错误抑制 (`2>/dev/null || true`)

## 修复逻辑
CI 分析报告指出模式18（浅克隆后 checkout 指定 commit 失败）。虽然前一个修复已通过 `git fetch origin ${VERSION}` 解决了主仓库的 checkout 问题，但 `--recurse-submodules --shallow-submodules` 在初始浅克隆时已将子模块克隆到其默认分支 HEAD，而非目标版本 `22fca04` 所引用的子模块 commit。后续 `git submodule update --init --recursive --depth 1 2>/dev/null || true` 因子模块已存在（但版本不匹配）且错误被抑制，导致子模块代码不完整，最终 cmake 构建失败。

修复方案：移除初始 clone 的 `--recurse-submodules --shallow-submodules`，仅在主仓库 checkout 到正确版本后，由 `git submodule update --init --recursive --depth 1` 首次浅克隆各子模块至目标 commit——与仓库中其他所有 Dockerfile 的模式一致。同时移除 `2>/dev/null || true` 以确保子模块更新失败时能及时发现。

## 潜在风险
- 如果 `git submodule update --init --recursive --depth 1` 因网络问题失败，现在会直接暴露错误（之前被静默跳过），这是正确的行为
- 子模块采用 `--depth 1` 浅克隆，如子模块数量多或体积大，首次克隆可能耗时较长，但不会比之前 `--recurse-submodules` 方案更差