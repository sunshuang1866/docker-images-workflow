# 修复摘要

## 修复的问题
Dockerfile 的 `dnf install` 列表中遗漏了 `grpc-devel` 包，导致 Ceph 21.3.0 CMake 配置阶段因找不到 `grpc++` pkg-config 模块而失败。

## 修改的文件
- `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`: 在 `dnf install` 命令末尾添加了 `grpc-devel` 包

## 修复逻辑
CI 分析报告指出 Ceph 21.3.0 的 `src/CMakeLists.txt:1055` 通过 `pkg_check_modules` 强制要求 `grpc++` 包（gRPC C++ 开发库），但 Dockerfile 的依赖安装列表中缺少对应的开发包。在 openEuler 24.03-LTS-SP3 上，`grpc-devel` 是提供 `grpc++.pc` pkg-config 模块的标准包名，补充后 CMake 可以正确找到该依赖并完成配置。

## 潜在风险
`grpc-devel` 作为标准开发包，其引入的额外依赖（如 `grpc`、`protobuf` 等库）与 Ceph 的构建需求一致，不会与现有依赖产生冲突。无其他风险。