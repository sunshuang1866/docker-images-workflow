# 修复摘要

## 修复的问题
ceph 21.3.0 编译时 cmake 配置阶段找不到 `grpc++` 包，因 Dockerfile 的 `dnf install` 缺少 gRPC C++ 开发依赖。

## 修改的文件
- `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`: 在 `dnf install -y` 步骤中新增 `grpc-devel protobuf-devel abseil-cpp-devel` 三个包。

## 修复逻辑
CI 分析报告指出 cmake 在 `pkg_check_modules(grpc++)` 时找不到 `grpc++` 包，根因是 Dockerfile 未安装 gRPC C++ 开发库。ceph 21.3.0 相比之前的 20.3.0 版本新增了对 gRPC 的构建依赖。在 openEuler 上，对应的开发包为 `grpc-devel`，其依赖链包含 `protobuf-devel` 和 `abseil-cpp-devel`，一并添加以确保链接阶段也能通过。

## 潜在风险
- 如果 openEuler 24.03-LTS-SP3 仓库中的 gRPC 版本不满足 ceph 21.3.0 的最低版本要求，构建可能仍会失败（对应分析报告中的方向 2），届时需要在 Dockerfile 中增加从源码编译安装 gRPC 的步骤。当前修复先尝试方向 1（仓库安装），风险可控。