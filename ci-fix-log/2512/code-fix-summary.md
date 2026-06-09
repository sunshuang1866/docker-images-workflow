# 修复摘要

## 修复的问题
修复 3FS Dockerfile 中的三个构建错误：运行时包名不存在（boost-foundation）、缺少构建依赖（libevent-devel）、git 浅克隆与 commit checkout 不兼容。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 三处修改（见下方详情）

## 修改详情

### 1. 移除不存在的 boost-foundation 包（第 41 行）
- **问题**: `boost-foundation` 在 openEuler 24.03-LTS-SP3 yum 仓库中不存在，导致 `yum install` 返回 exit code 1
- **修复**: 从运行时 `yum install` 列表中移除 `boost-foundation`

### 2. 添加 libevent-devel 构建依赖（第 6 行）
- **问题**: folly 子模块 cmake 配置时报 `Could NOT find libevent`，缺少 `libevent-devel` 构建依赖
- **修复**: 在 build 阶段 `yum install` 命令中追加 `libevent-devel`

### 3. 修复 git 浅克隆与版本切换不兼容（第 22-24 行）
- **问题**: `git clone --depth 1` 浅克隆仅包含最新提交，无法切换到指定的 commit `22fca04`；`2>/dev/null || true` 静默抑制了 checkout 失败
- **修复**: 去除 `--depth 1` 和 `--shallow-submodules` 参数，使用完整克隆；去除 `2>/dev/null || true` 和 `--depth 1`，让 checkout/submodule update 失败时显式终止构建

## 修复逻辑
三个修复分别对应分析报告中的三个根因方向（置信度：高/中/中），均为 Dockerfile 内新增代码的依赖声明和构建命令错误，不涉及其他文件。

## 潜在风险
- `libevent-devel` 在 openEuler 24.03-LTS-SP3 仓库中应存在，但若其包名略有不同（如 `libevent`），可能仍需调整
- 去除 `--depth 1` 全量克隆会增加构建时间和网络流量，但这是确保 commit checkout 正确的必要代价