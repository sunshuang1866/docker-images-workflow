# 修复摘要

## 修复的问题
Dockerfile 中 `git clone --branch v${VERSION}` 使用的标签 `v202103.Sumatra` 在上游 SeisSol/SeisSol 仓库中不存在（实际标签为 `202103_Sumatra`），导致构建失败。同时修复了 `LD_LIBRARY_PATH` 自引用未定义变量的 BuildKit 警告。

## 修改的文件
- `HPC/seissol/202103.Sumatra/24.03-lts-sp3/Dockerfile`: 三处修改

## 修复逻辑

1. **标签名修正**（根因修复，对应分析报告"方向 1"）：
   - 通过 GitHub API (`https://api.github.com/repos/SeisSol/SeisSol/git/refs/tags`) 确认上游 SeisSol 仓库的实际标签名为 `202103_Sumatra`（下划线分隔，无 `v` 前缀），而非 Dockerfile 中原使用的 `v202103.Sumatra`。
   - 已通过 `git ls-remote --tags https://github.com/SeisSol/SeisSol.git` 二次确认标签 `202103_Sumatra` 存在（commit `e1a02aabe401fd8cb985d57d87ac4e717437ddc0`）。
   - 修改：`ARG VERSION=202103.Sumatra` → `ARG VERSION=202103_Sumatra`，并将 `--branch v${VERSION}` → `--branch ${VERSION}`。

2. **LD_LIBRARY_PATH 警告修复**（对应分析报告"方向 2"，附加发现）：
   - 第 96 行 `$LD_LIBRARY_PATH` 在运行时阶段自引用了未定义变量，改为 `${LD_LIBRARY_PATH:-}` 消除 BuildKit `UndefinedVar` 警告。

## 潜在风险
无。修改仅涉及变量值修正和变量引用方式的规范化，不影响构建逻辑和运行时行为。