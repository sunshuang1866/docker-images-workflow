# 修复摘要

## 修复的问题
Ceph 21.3.0 构建失败：CMake 配置阶段缺少 Protobuf 依赖，以及两个 BuildKit 警告（`FROM as` 小写、`LD_LIBRARY_PATH` 自引用未定义变量）。

## 修改的文件
- `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`: 
  1. 在 `dnf install` 列表中添加了 `protobuf-devel protobuf-compiler`（第 23 行）
  2. 将 `FROM $BASE as builder` 改为 `FROM $BASE AS builder`（第 2 行）
  3. 将 `$LD_LIBRARY_PATH` 改为 `${LD_LIBRARY_PATH:-}`（第 48 行）

## 修复逻辑
1. **主修复（protobuf）**：CI 报错 `Could NOT find Protobuf`，根因是 Dockerfile 中 `dnf install` 遗漏了 `protobuf-devel` 和 `protobuf-compiler` 包，导致 Ceph 21.3.0 的 CMake 配置失败。补充这两个包即可满足 Ceph 对 Protobuf 的编译时依赖。
2. **次要修复（AS 大写）**：BuildKit 建议 `FROM ... AS ...` 中的 `AS` 应大写，将 `as` 改为 `AS`。
3. **次要修复（LD_LIBRARY_PATH）**：`ENV` 指令中 `$LD_LIBRARY_PATH` 首次定义时自引用了一个未定义的变量，使用 `${LD_LIBRARY_PATH:-}` 语法在变量未定义时提供空默认值。

## 潜在风险
- `protobuf-devel` 和 `protobuf-compiler` 的版本需与 openEuler 24.03-LTS-SP3 仓库中的版本一致。若仓库中版本过旧导致与 Ceph 21.3.0 不兼容，构建仍可能失败（但 CMake 检测版本通常在前，当前日志仅显示 not found 而非版本不匹配，风险较低）。
- `${LD_LIBRARY_PATH:-}` 的改动在 Dockerfile 上下文中有明确预期行为，不影响功能。