# 修复摘要

## 修复的问题
`git clone --depth 1` 浅克隆后无法 checkout 指定 commit hash `22fca04`，且错误被 `|| true` 静默掩盖，导致构建使用错误的源码版本。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`: 将 `git clone --recurse-submodules --depth 1 --shallow-submodules` 改为完整克隆（去除 `--depth 1` 和 `--shallow-submodules`），去除 checkout 和 submodule update 的 `2>/dev/null || true` 错误抑制，去除 submodule update 的 `--depth 1` 参数。

## 修复逻辑
分析报告指出 CI 在两个架构（x86-64、aarch64）的下游构建 job 均失败，根因是 `--depth 1` 浅克隆只拉取最新一次提交，后续 `git checkout 22fca04` 无法在浅克隆中找到该 commit 而失败。`2>/dev/null || true` 进一步掩盖了错误，导致 cmake 构建使用了默认分支 HEAD 的代码而非目标版本。

修复采用方向 1（高置信度）：
1. 去除 `--depth 1` 执行完整克隆，确保 commit hash `22fca04` 在本地仓库中可访问
2. 去除 `--shallow-submodules`（仅对浅克隆有意义）
3. 去除 `2>/dev/null || true`，让 checkout 失败时构建立即终止，避免使用错误代码

## 潜在风险
- 完整克隆会增加构建时间和网络流量（3fs 仓库及其 submodule 的完整历史）
- 无其他风险