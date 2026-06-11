# 修复摘要

## 修复的问题
Ceph 21.3.0 CMake 配置阶段找不到 Protobuf 库和头文件，导致构建失败。

## 修改的文件
- `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`: 在 `dnf install` 依赖列表（第20行）中补充了 `protobuf-devel` 和 `protobuf-compiler` 两个包。

## 修复逻辑
CI 分析报告指出，Dockerfile 中 `dnf install` 命令遗漏了 Protobuf 相关的 `-devel` 包，而 Ceph 21.3.0 的 CMake 构建系统（`src/CMakeLists.txt:1029`）通过 `find_package(Protobuf ...)` 强制要求 Protobuf。`protobuf-devel` 提供 `Protobuf_INCLUDE_DIR` 和 `Protobuf_LIBRARIES`，`protobuf-compiler` 提供 `protoc` 编译器，补齐这两个依赖即可让 CMake 配置阶段正确找到 Protobuf。这是修复 CI 失败分析报告中"方向 1（置信度: 高）"的根因。

## 潜在风险
无。这两个包是 Ceph 构建系统的标准依赖，在 openEuler 24.03-LTS-SP3 仓库中可用。未修改 `pr.changed_files` 列表之外的任何文件。