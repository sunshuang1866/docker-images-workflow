# 修复摘要

## 修复的问题
Dockerfile 的 `dnf install` 缺少 `protobuf-devel` 和 `protobuf-compiler` 包，导致 ceph CMake 配置阶段 `find_package(Protobuf)` 失败。

## 修改的文件
- `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`: 在第 14 行的 `dnf install` 包列表中追加了 `protobuf-devel protobuf-compiler`

## 修复逻辑
CI 分析报告指出失败根因是 Dockerfile 第 5-14 行的 `dnf install` 命令遗漏了 `protobuf-devel`，导致 ceph 21.3.0 版本的 CMake 构建（`src/CMakeLists.txt:1029` 处 `find_package(Protobuf)`）找不到 Protobuf 库和头文件。在原位置追加 `protobuf-devel protobuf-compiler` 是最小化的精确修复。

## 潜在风险
无。该改动仅新增所需依赖包，不影响已有包和后续流程。