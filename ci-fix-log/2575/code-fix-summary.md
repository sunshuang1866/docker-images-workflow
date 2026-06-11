# 修复摘要

## 修复的问题
Ceph 21.3.0 构建时 CMake 找不到 `grpc++` 包，因 Dockerfile 的 `dnf install` 遗漏了 `grpc-devel` 和 `protobuf-devel`。

## 修改的文件
- `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`: 在 `dnf install` 命令（第20行）中补充 `grpc-devel protobuf-devel`

## 修复逻辑
Ceph 21.3.0 相比 20.3.0 新增了 gRPC 构建时依赖，其 CMake 通过 `pkg_check_modules` 查找 `grpc++` 模块。Dockerfile 中未安装 `grpc-devel`（提供 `grpc++.pc` pkgconfig 文件及头文件），导致 CMake 配置阶段失败。补充 `grpc-devel` 和 `protobuf-devel`（gRPC 的 protobuf 依赖）后，CMake 可正常找到所需模块。

## 潜在风险
无。`grpc-devel` 和 `protobuf-devel` 在 openEuler 24.03-LTS-SP3 仓库中为标准包，仅用于编译阶段，不影响运行时镜像大小。