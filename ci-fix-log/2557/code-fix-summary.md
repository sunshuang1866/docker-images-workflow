# 修复摘要

## 修复的问题
Dockerfile 中使用了 openEuler RPM 仓库中不存在的包名 `boost-foundation`，导致 `yum install` 失败；同时缺少 `libevent-devel` 致 CMake 配置阶段找不到 libevent。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`:
  - **第 6 行**：添加 `libevent-devel`（修复 CMake `FindLibEvent.cmake` 错误）
  - **第 41 行**：移除不存在的 `boost-foundation`，将 `boost-filesystem boost-system boost-program-options` 合并为 `boost-devel`（openEuler 中 boost 开发库统一由 `boost-devel` 提供）

## 修复逻辑
1. **`boost-foundation`**：该包名在任何 openEuler 版本的 RPM 仓库中均不存在，是致命错误的直接原因。openEuler 的 boost 库统一由 `boost-devel` 提供（参考仓库内 LizardFS、Hyperscan、QMCpack 等其他 Dockerfile 的做法）。
2. **`boost-filesystem/boost-system/boost-program-options`**：openEuler 不提供独立的 boost 子组件 RPM 包，均包含在 `boost-devel` 中，故合并。
3. **`libevent-devel`**：分析报告步骤 #10 显示 CMake 配置阶段在 `FindLibEvent.cmake:68` 报错，确认 folly 需要 libevent 开发头文件。

## 潜在风险
- 由于当前 Dockerfile 是单阶段构建（非多阶段），第 6 行已安装的 `boost-devel` 已包含运行时库，第 41 行再次安装 `boost-devel` 为冗余操作，但无害。
- `git clone --depth 1` + commit hash checkout 的兼容性问题（模式18）在原始 PR 中已通过 `|| true` 处理，未作额外修改。