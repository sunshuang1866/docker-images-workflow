# 修复摘要

## 修复的问题
Dockerfile 构建 Ceph 时 CMake 配置阶段找不到 `grpc_cpp_plugin` 可执行文件，导致构建失败。

## 修改的文件
- `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`: 在 `dnf install` 命令中新增 `grpc-plugins` 包，提供 `grpc_cpp_plugin` 可执行文件。

## 修复逻辑
CI 分析报告指出 Ceph 21.3.0 的构建系统在 CMake 配置阶段需要通过 `grpc_cpp_plugin` 从 `.proto` 文件生成 C++ gRPC 代码，但 Dockerfile 的 `dnf install` 中缺少 `grpc-plugins` 包，导致 `find_program(grpc_cpp_plugin)` 失败。修复方案为在 `dnf install` 命令末尾补充 `grpc-plugins` 包，使该可执行文件在构建时可用。

## 潜在风险
- `grpc-plugins` 包的版本需与已安装的 gRPC 1.60.0 兼容（openEuler 24.03-LTS-SP3 仓库中应为匹配版本）。
- 若仓库中 `grpc-plugins` 包名有差异，需根据 `dnf provides */grpc_cpp_plugin` 的实际结果调整包名。