# 修复摘要

## 修复的问题
Dockerfile 缺少 gRPC 开发库导致 cmake 配置阶段找不到 `grpc++` 包，同时修复了 FROM 指令大小写不规范和 LD_LIBRARY_PATH 自引用未定义变量两个次要问题。

## 修改的文件
- `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`:
  - 第 2 行: `as builder` → `AS builder`（修复 BuildKit FromAsCasing 警告）
  - 第 24 行: 在 `dnf install -y` 中新增 `grpc-devel protobuf-devel` 依赖（修复 cmake 找不到 grpc++ 的构建失败）
  - 第 48 行: `$LD_LIBRARY_PATH` → `${LD_LIBRARY_PATH:-}`（修复模式20：自引用未定义变量）

## 修复逻辑
CI 分析报告指出三个问题：
1. **主因**（dependency-error）: ceph 21.3.0 编译时需要 `grpc++` 开发库，但 Dockerfile 的 `dnf install` 列表中遗漏了 `grpc-devel` 和 `protobuf-devel`。在 openEuler 24.03-lts-sp3 上补充这两个 RPM 包以提供 `grpc++` pkg-config 模块。
2. **次要问题**: FROM 指令中 `as` 应为大写 `AS`，符合 Dockerfile 最佳实践。
3. **次要问题**: ENV 指令中 `$LD_LIBRARY_PATH` 自引用了未定义的变量，改为 `${LD_LIBRARY_PATH:-}` 在变量未定义时使用空值。

## 潜在风险
- `grpc-devel` 和 `protobuf-devel` 是推测的包名，openEuler 24.03-lts-sp3 仓库中可能使用不同的包名（如 `grpc++-devel`），若构建仍失败需确认仓库中的精确包名。
- 这些包可能引入额外的运行时依赖，但由于构建阶段（builder）和运行阶段分离（如后续阶段使用多阶段构建），运行时镜像不应受额外构建依赖影响。