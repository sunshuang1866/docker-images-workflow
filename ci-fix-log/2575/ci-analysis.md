# CI 失败分析报告

## 基本信息
- PR: #2575 — 【自动升级】ceph容器镜像升级至21.3.0版本
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式10
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#12 286.3 -- Checking for module 'grpc++'
#12 286.3 --   Package 'grpc++', required by 'virtual:world', not found
#12 286.3 CMake Error at /usr/share/cmake/Modules/FindPkgConfig.cmake:607 (message):
#12 286.3   A required package was not found
#12 286.3 Call Stack (most recent call first):
#12 286.3   /usr/share/cmake/Modules/FindPkgConfig.cmake:829 (_pkg_check_modules_internal)
#12 286.3   src/CMakeLists.txt:1055 (pkg_check_modules)
#12 286.3
#12 286.3
#12 286.3 -- Configuring incomplete, errors occurred!
#12 286.4 + exit 1
#12 ERROR: process "/bin/sh -c git clone -b v${VERSION} --recursive --depth 1 https://github.com/ceph/ceph.git     && cd ceph     && ./do_cmake.sh -DCMAKE_BUILD_TYPE=Release -DWITH_TESTS=OFF     && cd build     && ninja -j$(nproc)     && ninja install" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `src/CMakeLists.txt:1055`（Ceph 上游构建脚本，非 PR 新增文件）
- 失败原因: Ceph 21.3.0 的 CMake 构建配置依赖 `grpc++`（gRPC C++ 库），但 Dockerfile 的 `dnf install` 步骤遗漏了 `grpc-devel` 包，导致 pkg-config 找不到该模块，CMake 配置阶段终止

### 与 PR 变更的关联
PR 新增了整个 `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`（54 行全新文件），其中的 `dnf install` 命令列出了大量编译依赖，但遗漏了 Ceph 21.3.0 所需的关键包 `grpc-devel`（可能还需 `protobuf-devel`、`abseil-cpp-devel` 等 gRPC 相关依赖）。该失败完全由 PR 引入的新 Dockerfile 中依赖声明不完整导致。

**附注**：日志尾部出现的两个 BuildKit 警告（`FromAsCasing` 和 `UndefinedVar`）为风格警告，**非本次失败原因**。其中 `UndefinedVar` 警告涉及 Dockerfile 第 47 行的 `ENV LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH`，可参考模式20通过 `${LD_LIBRARY_PATH:-}` 语法消除，但不应作为修复的核心。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 `dnf install` 命令中补充 `grpc-devel` 包。openEuler 24.03-LTS-SP3 上 gRPC 相关包名通常为 `grpc-devel` 或 `grpc-cpp-devel`，若该包还依赖 `abseil-cpp-devel`、`protobuf-devel`，也需一并添加。可参考 Ceph 21.3.0 的上游构建文档确认完整依赖列表。

### 方向 2（置信度: 中）
Ceph 21.3.0 相比之前的 20.3.0 可能新增了对 gRPC 的构建时依赖。如果在 SP3 仓库中找不到 `grpc-devel` 包，可能需要通过 `pip install grpcio grpcio-tools` 安装 Python gRPC 工具链，或从源码编译 gRPC（参考 Ceph 官方 `install-deps.sh` 脚本）。

## 需要进一步确认的点
1. openEuler 24.03-LTS-SP3 仓库中 `grpc-devel`（或 `grpc-cpp-devel`）包的确切名称和可用性
2. Ceph 21.3.0 是否还需要 `protobuf-devel`（日志显示运行时 `libprotobuf.so` 已存在，但开发头文件可能缺失）
3. 是否有其他 Ceph 21.3.0 新增的依赖在 Dockerfile 中被遗漏（可通过对比已有 ceph 20.3.0 Dockerfile 的依赖列表来排查）
