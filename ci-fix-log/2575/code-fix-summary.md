# 修复摘要

## 修复的问题
CI 构建失败：cmake 找不到 Protobuf（`Could NOT find Protobuf`），同时修复 Dockerfile 中的 `UndefinedVar` 和 `FromAsCasing` 警告。

## 修改的文件
- `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`:
  1. 在 `dnf install` 列表中添加 `protobuf-devel` 和 `protobuf-compiler` 包（第 24 行）
  2. 将 `as builder` 改为 `AS builder`（第 2 行），消除大小写不一致警告
  3. 将 `ENV LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH` 改为 `ENV LD_LIBRARY_PATH=/usr/local/lib64:${LD_LIBRARY_PATH:-}`（第 48 行），消除未定义变量警告

## 修复逻辑
- **根因**：Dockerfile 的 `dnf install` 未包含 `protobuf-devel`，导致 ceph cmake 配置阶段 `find_package(Protobuf)` 失败。ceph 21.3.0 构建系统强制要求 Protobuf 作为编译依赖，缺少该包会导致 cmake 配置报错退出。
- 同时修复了分析报告中指出的两个次要问题：`FromAsCasing` 大小写不一致警告和 `UndefinedVar` 自引用未定义变量警告。

## 潜在风险
无。添加的 `protobuf-devel` 和 `protobuf-compiler` 是 openEuler 仓库中的标准包，不会引入兼容性问题。`ENV` 和 `FROM ... AS` 的修改是纯语法层面的修正，不影响运行时行为。