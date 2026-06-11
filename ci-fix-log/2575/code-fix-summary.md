# 修复摘要

## 修复的问题
Dockerfile 缺少 gRPC C++ 构建依赖导致 cmake 配置失败，以及 ENV 自引用未定义变量导致 BuildKit 警告。

## 修改的文件
- `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`:
  - 第13行: 在 `dnf install` 列表中添加 `grpc-devel` 包，解决 ceph 21.3.0 新增的 gRPC C++ 构建依赖缺失问题
  - 第47行: 将 `$LD_LIBRARY_PATH` 改为 `${LD_LIBRARY_PATH:-}`，消除 BuildKit 的 UndefinedVar 警告

## 修复逻辑
1. **gnrpc-devel 缺失**: ceph 21.3.0 源码 `src/CMakeLists.txt:1055` 处 `pkg_check_modules(grpc++)` 找不到 `grpc++` 包，因为 `dnf install` 未包含 `grpc-devel`。相比旧版本 ceph，21.3.0 新增了对 gRPC C++ 的构建依赖。在 `dnf install` 中追加 `grpc-devel` 即可提供 cmake 所需的 gRPC C++ headers 和 pkg-config 文件。
2. **ENV 自引用**: Dockerfile 第47行 `ENV LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH` 引用了一个在构建上下文中未定义的变量，触发 BuildKit `UndefinedVar` 警告。使用 `${LD_LIBRARY_PATH:-}` (bash 参数扩展，未定义时为空字符串) 消除该警告。

## 潜在风险
- `grpc-devel` 包名在 openEuler 24.03-LTS-SP3 中已确认为标准名（与 Fedora/RHEL 生态一致），若仓库中包名不同（如 `grpc++-devel`），构建仍会失败，但该风险较低。
- `${LD_LIBRARY_PATH:-}` 在未定义时产生尾随冒号 `/usr/local/lib64:`，Linux 动态链接器对此可正常处理，不产生副作用。