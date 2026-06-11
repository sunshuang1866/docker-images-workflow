# CI 失败分析报告

## 基本信息
- PR: #2575 — 【自动升级】ceph容器镜像升级至21.3.0版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式10
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#12 422.4 -- Checking for module 'grpc++'
#12 422.4 --   Package 'grpc++', required by 'virtual:world', not found
#12 422.4 CMake Error at /usr/share/cmake/Modules/FindPkgConfig.cmake:607 (message):
#12 422.4   A required package was not found
#12 422.4 Call Stack (most recent call first):
#12 422.4   /usr/share/cmake/Modules/FindPkgConfig.cmake:829 (_pkg_check_modules_internal)
#12 422.4   src/CMakeLists.txt:1055 (pkg_check_modules)
#12 422.4
#12 422.4
#12 422.5 -- Configuring incomplete, errors occurred!
#12 422.5 + exit 1
#12 ERROR: process "/bin/sh -c git clone -b v${VERSION} --recursive --depth 1 https://github.com/ceph/ceph.git     && cd ceph     && ./do_cmake.sh -DCMAKE_BUILD_TYPE=Release -DWITH_TESTS=OFF     && cd build     && ninja -j$(nproc)     && ninja install" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`:41（`do_cmake.sh` 执行阶段，对应 cmake 配置 step）
- 失败原因: ceph 21.3.0 的 CMake 构建系统通过 `pkg_check_modules` 查找 `grpc++` 包，但 Dockerfile 的 `dnf install` 步骤遗漏安装了 gRPC C++ 开发库（openEuler 上包名通常为 `grpc-devel` 或 `grpc-plugins`），导致 cmake 配置阶段失败。

### 与 PR 变更的关联
本 PR 是新增 ceph 21.3.0 版本（Dockerfile 为新文件），失败由该 Dockerfile 中 `dnf install` 依赖列表不完整直接触发。与历史版本无关——这是首次为 ceph 21.3.0 编写构建文件，依赖项未完整梳理。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 `dnf install -y` 步骤中补充 gRPC C++ 相关的开发包。ceph 21.3.0 编译需要 gRPC 支持，需安装 `grpc-devel`（以及可能的 `grpc-plugins`、`protobuf-devel`）。具体需确认 openEuler 24.03-LTS-SP3 仓库中提供 gRPC C++ 开发库的包名，并将其添加到依赖列表中。

### 方向 2（置信度: 中）
如果 openEuler 24.03-LTS-SP3 仓库中 gRPC 版本不满足 ceph 21.3.0 的最低要求（通常在 cmake 中设定了版本阈值），则需要在 Dockerfile 中增加从源码编译安装 gRPC 的步骤。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP3 中 gRPC C++ 开发库的准确包名（`grpc-devel`、`grpc++-devel` 或其他）
- ceph 21.3.0 对 gRPC 的最低版本要求，以及 openEuler 仓库中 gRPC 的版本是否满足
- cmake 报错中仅提及 `grpc++`，但可能有其他连带缺失的依赖（如 `abseil-cpp-devel`、`protobuf-devel` 等），需在补充 grpc 依赖后重新构建验证
